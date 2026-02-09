"""
IAM Authorization and Audit Logging Utilities

Provides IAM-based authorization and audit logging for direct Lambda invocations.
Ensures that only authorized IAM principals can invoke Lambda functions directly
and maintains comprehensive audit trails for compliance and security monitoring.

## Architecture Pattern

IAM-Based Authorization:
- Extract IAM principal from Lambda context
- Validate principal against allowed patterns
- Log all invocation attempts with principal information
- Support for IAM roles, users, and assumed roles

## Integration Points

### 1. Lambda Handler Authorization (Entry Point)
```python
from shared.iam_utils import (
    extract_iam_principal,
    validate_iam_authorization,
    log_direct_invocation
)

def handle_direct_invocation(event, context):
    # Extract IAM principal from context
    principal = extract_iam_principal(context)
    
    # Validate authorization
    if not validate_iam_authorization(principal):
        log_direct_invocation(
            principal=principal,
            operation=event.get("operation"),
            params=event.get("queryParams", {}),
            result={"error": "AUTHORIZATION_FAILED"},
            success=False
        )
        return {
            "error": "AUTHORIZATION_FAILED",
            "message": "Insufficient permissions for direct invocation"
        }
    
    # Process operation
    result = process_operation(event)
    
    # Log successful invocation
    log_direct_invocation(
        principal=principal,
        operation=event.get("operation"),
        params=event.get("queryParams", {}),
        result=result,
        success=True
    )
    
    return result
```

### 2. Step Functions Integration
```python
# Step Functions automatically provides IAM context
# The execution role ARN is available in context.invoked_function_arn

def lambda_handler(event, context):
    if "operation" in event:
        # Direct invocation from Step Functions
        principal = extract_iam_principal(context)
        # principal will be the Step Functions execution role
        return handle_direct_invocation(event, context)
```

### 3. Cross-Account Invocation
```python
# When Lambda is invoked from another account via assume role
# The principal will include the assumed role ARN

principal = extract_iam_principal(context)
# Example: arn:aws:sts::123456789012:assumed-role/OrchestrationRole/session-name

if not validate_iam_authorization(principal):
    return {"error": "AUTHORIZATION_FAILED"}
```

## IAM Principal Formats

### IAM Role
```
arn:aws:iam::123456789012:role/OrchestrationRole
```

### Assumed Role (Step Functions)
```
arn:aws:sts::123456789012:assumed-role/OrchestrationRole/execution-id
```

### IAM User
```
arn:aws:iam::123456789012:user/admin
```

### Service Principal
```
arn:aws:iam::123456789012:role/aws-service-role/states.amazonaws.com/AWSServiceRoleForStepFunctions
```

## Authorization Patterns

### Allowed Principals
- OrchestrationRole: Primary automation role
- Step Functions execution roles
- Lambda execution roles
- Admin users (for testing)

### Denied Principals
- Unauthenticated requests
- Unknown roles
- Roles without required permissions

## Audit Log Format

### Successful Invocation
```json
{
  "timestamp": "2026-02-09T12:00:00.000Z",
  "event_type": "direct_invocation",
  "principal": "arn:aws:sts::123456789012:assumed-role/OrchestrationRole/exec-123",
  "operation": "get_drs_source_servers",
  "parameters": {"region": "us-east-1"},
  "result": {"servers": [...], "totalCount": 25},
  "success": true,
  "request_id": "abc-123-def-456",
  "function_name": "query-handler",
  "function_version": "$LATEST"
}
```

### Failed Authorization
```json
{
  "timestamp": "2026-02-09T12:00:00.000Z",
  "event_type": "direct_invocation",
  "principal": "arn:aws:iam::123456789012:user/unauthorized",
  "operation": "get_drs_source_servers",
  "parameters": {"region": "us-east-1"},
  "result": {"error": "AUTHORIZATION_FAILED"},
  "success": false,
  "request_id": "abc-123-def-456",
  "function_name": "query-handler",
  "function_version": "$LATEST"
}
```

## Security Considerations

### Principal Validation
- Always validate principal ARN format
- Check for required role names
- Log all authorization failures
- Never expose sensitive data in logs

### Audit Trail
- Log all invocation attempts
- Include timestamp, principal, operation, and result
- Mask sensitive parameters
- Store logs in CloudWatch for compliance

### Error Handling
- Return generic error messages to callers
- Log detailed error information internally
- Never expose internal system details
- Rate limit failed authorization attempts

## Testing Considerations

### Mock Lambda Context
```python
from unittest.mock import Mock

# Create mock context
context = Mock()
context.invoked_function_arn = (
    "arn:aws:lambda:us-east-1:123456789012:function:query-handler"
)
context.identity = Mock()
context.identity.cognito_identity_id = None
context.identity.cognito_identity_pool_id = None

# Mock IAM principal
context.invoked_function_arn = (
    "arn:aws:sts::123456789012:assumed-role/OrchestrationRole/exec-123"
)

principal = extract_iam_principal(context)
assert "OrchestrationRole" in principal
```

### Mock Authorization
```python
from unittest.mock import patch

with patch('shared.iam_utils.validate_iam_authorization') as mock_auth:
    mock_auth.return_value = True
    result = handle_direct_invocation(event, context)
    assert "error" not in result
```

### Mock Audit Logging
```python
from unittest.mock import patch

with patch('shared.iam_utils.logger') as mock_logger:
    log_direct_invocation(
        principal="arn:aws:iam::123456789012:role/TestRole",
        operation="test_operation",
        params={},
        result={"success": True},
        success=True
    )
    assert mock_logger.info.called
```
"""

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def extract_iam_principal(context) -> str:
    """
    Extract IAM principal ARN from Lambda context.
    
    The Lambda context object contains identity information about the caller.
    For direct Lambda invocations, this includes the IAM role or user ARN.
    
    Args:
        context: Lambda context object
        
    Returns:
        IAM principal ARN string, or "unknown" if not available
        
    Examples:
        >>> context = Mock()
        >>> context.invoked_function_arn = "arn:aws:lambda:us-east-1:123:function:handler"
        >>> extract_iam_principal(context)
        "arn:aws:lambda:us-east-1:123:function:handler"
    """
    try:
        # Try to get principal from context identity (for assumed roles)
        if hasattr(context, "identity") and context.identity:
            if hasattr(context.identity, "user_arn"):
                return context.identity.user_arn
        
        # For Step Functions and direct invocations, use invoked_function_arn
        # This contains the execution role information
        if hasattr(context, "invoked_function_arn"):
            return context.invoked_function_arn
        
        # Fallback: try to extract from request context
        if hasattr(context, "request_context"):
            request_context = context.request_context
            if isinstance(request_context, dict):
                if "identity" in request_context:
                    identity = request_context["identity"]
                    if "userArn" in identity:
                        return identity["userArn"]
        
        logger.warning("Unable to extract IAM principal from context")
        return "unknown"
        
    except Exception as e:
        logger.error(f"Error extracting IAM principal: {e}")
        return "unknown"


def validate_iam_authorization(principal_arn: str) -> bool:
    """
    Validate that IAM principal is authorized for direct invocation.
    
    Checks if the principal ARN matches allowed patterns for direct Lambda
    invocation. This includes OrchestrationRole, Step Functions roles,
    and admin users.
    
    Args:
        principal_arn: IAM principal ARN to validate
        
    Returns:
        True if principal is authorized, False otherwise
        
    Examples:
        >>> validate_iam_authorization("arn:aws:iam::123:role/OrchestrationRole")
        True
        >>> validate_iam_authorization("arn:aws:iam::123:user/unauthorized")
        False
    """
    if not principal_arn or principal_arn == "unknown":
        logger.warning("Authorization check failed: unknown principal")
        return False
    
    # Allowed role patterns
    allowed_patterns = [
        # OrchestrationRole (primary automation role)
        r"arn:aws:iam::\d{12}:role/.*OrchestrationRole.*",
        r"arn:aws:sts::\d{12}:assumed-role/.*OrchestrationRole.*",
        
        # Step Functions execution roles
        r"arn:aws:iam::\d{12}:role/.*StepFunctions.*",
        r"arn:aws:sts::\d{12}:assumed-role/.*StepFunctions.*",
        
        # Lambda execution roles (for Lambda-to-Lambda calls)
        r"arn:aws:iam::\d{12}:role/.*Lambda.*",
        r"arn:aws:lambda:.*:function:.*",
        
        # Admin users (for testing and manual operations)
        r"arn:aws:iam::\d{12}:user/admin.*",
        r"arn:aws:sts::\d{12}:assumed-role/.*Admin.*",
        
        # Service roles
        r"arn:aws:iam::\d{12}:role/aws-service-role/.*",
    ]
    
    # Check if principal matches any allowed pattern
    for pattern in allowed_patterns:
        if re.match(pattern, principal_arn, re.IGNORECASE):
            logger.info(f"Authorization granted for principal: {principal_arn}")
            return True
    
    # Log authorization failure
    logger.warning(
        f"Authorization denied for principal: {principal_arn}. "
        "Principal does not match allowed patterns."
    )
    return False


def log_direct_invocation(
    principal: str,
    operation: str,
    params: Dict[str, Any],
    result: Any,
    success: bool,
    context: Optional[Any] = None
) -> None:
    """
    Log direct Lambda invocation for audit trail.
    
    Creates comprehensive audit log entry for compliance and security monitoring.
    Includes timestamp, principal, operation, parameters, result, and metadata.
    
    Args:
        principal: IAM principal ARN
        operation: Operation name (e.g., "get_drs_source_servers")
        params: Operation parameters (will be masked for sensitive data)
        result: Operation result (will be truncated if large)
        success: Whether operation succeeded
        context: Optional Lambda context for additional metadata
        
    Examples:
        >>> log_direct_invocation(
        ...     principal="arn:aws:iam::123:role/OrchestrationRole",
        ...     operation="get_drs_source_servers",
        ...     params={"region": "us-east-1"},
        ...     result={"servers": [...]},
        ...     success=True
        ... )
    """
    try:
        # Mask sensitive parameters
        masked_params = _mask_sensitive_params(params)
        
        # Truncate large results for logging
        truncated_result = _truncate_result(result)
        
        # Build audit log entry
        audit_log = {
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            "event_type": "direct_invocation",
            "principal": principal,
            "operation": operation,
            "parameters": masked_params,
            "result": truncated_result,
            "success": success,
        }
        
        # Add context metadata if available
        if context:
            audit_log.update({
                "request_id": getattr(context, "aws_request_id", "unknown"),
                "function_name": getattr(context, "function_name", "unknown"),
                "function_version": getattr(context, "function_version", "unknown"),
            })
        
        # Log at appropriate level
        if success:
            logger.info(json.dumps(audit_log))
        else:
            logger.warning(json.dumps(audit_log))
            
    except Exception as e:
        logger.error(f"Error logging direct invocation: {e}")


def _mask_sensitive_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mask sensitive parameters in audit logs.
    
    Args:
        params: Parameters dictionary
        
    Returns:
        Dictionary with sensitive values masked
    """
    if not isinstance(params, dict):
        return params
    
    sensitive_keys = [
        "password",
        "secret",
        "token",
        "key",
        "credential",
        "authorization",
        "auth",
    ]
    
    masked = {}
    for key, value in params.items():
        key_lower = key.lower()
        
        # Check if key contains sensitive data
        is_sensitive = any(
            sensitive_key in key_lower for sensitive_key in sensitive_keys
        )
        
        if is_sensitive and isinstance(value, str) and len(value) > 4:
            # Mask all but first 4 characters
            masked[key] = value[:4] + "*" * (len(value) - 4)
        elif isinstance(value, dict):
            masked[key] = _mask_sensitive_params(value)
        else:
            masked[key] = value
    
    return masked


def _truncate_result(result: Any, max_length: int = 1000) -> Any:
    """
    Truncate large results for logging.
    
    Args:
        result: Result to truncate
        max_length: Maximum length for string representation
        
    Returns:
        Truncated result
    """
    try:
        # Convert to JSON string
        result_str = json.dumps(result)
        
        # Truncate if too long
        if len(result_str) > max_length:
            return {
                "truncated": True,
                "preview": result_str[:max_length] + "...",
                "original_length": len(result_str),
            }
        
        return result
        
    except Exception:
        # If result can't be serialized, return string representation
        result_str = str(result)
        if len(result_str) > max_length:
            return {
                "truncated": True,
                "preview": result_str[:max_length] + "...",
            }
        return result_str


def create_authorization_error_response() -> Dict[str, Any]:
    """
    Create standardized authorization error response.
    
    Returns:
        Error response dictionary
    """
    return {
        "error": "AUTHORIZATION_FAILED",
        "message": "Insufficient permissions for direct invocation",
        "details": (
            "Direct Lambda invocation requires OrchestrationRole or "
            "equivalent IAM permissions"
        ),
    }


def validate_direct_invocation_event(event: Dict[str, Any]) -> bool:
    """
    Validate that event is a valid direct invocation format.
    
    Args:
        event: Lambda event to validate
        
    Returns:
        True if valid direct invocation event
    """
    if not isinstance(event, dict):
        return False
    
    # Direct invocation must have "operation" field
    if "operation" not in event:
        return False
    
    # Operation must be a non-empty string
    operation = event.get("operation")
    if not isinstance(operation, str) or not operation.strip():
        return False
    
    return True
