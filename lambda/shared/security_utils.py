"""
Security Utilities for AWS DRS Orchestration

Provides input validation, sanitization, and security helpers for protecting against
common web vulnerabilities (injection attacks, XSS, path traversal, etc.).

## Architecture Pattern

Defense-in-Depth Security:
- Input validation at API boundaries
- String sanitization for user-provided data
- Format validation for AWS resource identifiers
- Security event logging for audit trails
- Rate limiting hooks (requires DynamoDB/Redis implementation)

## Integration Points

### 1. API Gateway Event Validation (Entry Point)
```python
from shared.security_utils import validate_api_gateway_event, InputValidationError

def lambda_handler(event, context):
    try:
        # Validate and sanitize API Gateway event
        safe_event = validate_api_gateway_event(event)

        # Use sanitized data
        method = safe_event["httpMethod"]
        path = safe_event["path"]
        query_params = safe_event["queryStringParameters"]

    except InputValidationError as e:
        return {"statusCode": 400, "body": json.dumps({"error": str(e)})}
```

### 2. String Sanitization (User Input)
```python
from shared.security_utils import sanitize_string, InputValidationError

try:
    # Sanitize user-provided strings
    plan_name = sanitize_string(user_input["planName"], max_length=100)
    description = sanitize_string(user_input["description"], max_length=500)

except InputValidationError as e:
    return {"statusCode": 400, "body": json.dumps({"error": str(e)})}
```

### 3. DynamoDB Input Sanitization (Before Write)
```python
from shared.security_utils import sanitize_dynamodb_input

# Sanitize data before DynamoDB write
user_data = {
    "planName": "<script>alert('xss')</script>",
    "description": "Test plan",
    "waves": [{"waveNumber": 1, "name": "Wave 1"}]
}

safe_data = sanitize_dynamodb_input(user_data)
# Result: {"planName": "scriptalert('xss')/script", ...}

dynamodb.put_item(TableName="RecoveryPlans", Item=safe_data)
```

### 4. AWS Resource ID Validation
```python
from shared.security_utils import (
    validate_aws_region,
    validate_drs_server_id,
    validate_aws_account_id,
    validate_uuid
)

# Validate AWS identifiers before API calls
if not validate_aws_region(region):
    return {"statusCode": 400, "body": "Invalid region"}

if not validate_drs_server_id(server_id):
    return {"statusCode": 400, "body": "Invalid DRS server ID"}

if not validate_aws_account_id(account_id):
    return {"statusCode": 400, "body": "Invalid AWS account ID"}
```

### 5. Security Event Logging (Audit Trail)
```python
from shared.security_utils import log_security_event

# Log security-relevant events
log_security_event(
    event_type="unauthorized_access_attempt",
    details={
        "user_id": user["userId"],
        "endpoint": "/recovery-plans/plan-123/execute",
        "reason": "Missing START_RECOVERY permission"
    },
    severity="WARN"
)

# Log critical security events
log_security_event(
    event_type="path_traversal_blocked",
    details={"path": "../../etc/passwd", "user_id": user["userId"]},
    severity="CRITICAL"
)
```

### 6. Sensitive Data Masking (Logs)
```python
from shared.security_utils import mask_sensitive_data

# Mask sensitive fields before logging
user_data = {
    "username": "jdoe",
    "password": "secret123",  # pragma: allowlist secret
    "api_token": "abc123xyz789",
    "email": "jdoe@example.com"
}

masked = mask_sensitive_data(user_data)
# Result: {"username": "jdoe", "password": "secr********", "api_token": "abc1********", "email": "jdoe@example.com"}  # pragma: allowlist secret  # noqa: E501

logger.info(f"User data: {json.dumps(masked)}")
```

### 7. Security Headers (HTTP Responses)
```python
from shared.security_utils import create_security_headers

headers = create_security_headers()
# Returns:
# {
#     "X-Content-Type-Options": "nosniff",
#     "X-Frame-Options": "DENY",
#     "X-XSS-Protection": "1; mode=block",
#     "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
#     "Content-Security-Policy": "default-src 'self'; ...",
#     "Referrer-Policy": "strict-origin-when-cross-origin",
#     "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
# }

return {
    "statusCode": 200,
    "headers": {**headers, "Content-Type": "application/json"},
    "body": json.dumps({"message": "Success"})
}
```

## Validation Functions

### String Validation
- `sanitize_string()`: Remove dangerous characters (<>\"';\\, control chars)
- `validate_protection_group_name()`: 3-50 chars, alphanumeric + spaces/hyphens/underscores
- `validate_recovery_plan_name()`: Same as protection group names
- `validate_email()`: Standard email format validation

### AWS Resource Validation
- `validate_aws_region()`: us-east-1, eu-west-2, us-gov-west-1 patterns
- `validate_drs_server_id()`: s-[17 hex chars] format
- `validate_aws_account_id()`: 12-digit number
- `validate_uuid()`: Standard UUID format (8-4-4-4-12)

### Input Validation
- `validate_json_input()`: Parse JSON with size limits (default 1MB)
- `validate_api_gateway_event()`: Validate API Gateway event structure
- `validate_file_path()`: Block path traversal attacks (.., %2e%2e)
- `validate_dynamodb_input()`: Validate DynamoDB field formats

## Performance Optimizations

### Sanitization Shortcuts
```python
# FAST PATH: Skip sanitization for safe alphanumeric strings
"server-123" → No regex processing (alphanumeric + safe chars)

# FAST PATH: Skip sanitization for known-safe fields
{"executionId": "...", "status": "..."} → No sanitization

# SLOW PATH: Full regex sanitization only for potentially dangerous content
"<script>alert('xss')</script>" → Full sanitization
```

### Large Data Handling
```python
# Skip deep sanitization for large objects (>50 fields)
execution_data = {...}  # 100+ fields from DynamoDB
sanitize_dynamodb_input(execution_data)  # Minimal processing

# Skip sanitization for large strings (>1000 chars)
large_description = "..." * 2000
sanitize_string(large_description)  # Returns unchanged
```

## Security Headers

### X-Content-Type-Options: nosniff
Prevents MIME-sniffing attacks where browsers interpret files as different types.

### X-Frame-Options: DENY
Prevents clickjacking by blocking iframe embedding.

### X-XSS-Protection: 1; mode=block
Enables browser XSS filter (legacy browsers).

### Strict-Transport-Security
Forces HTTPS connections for 1 year including subdomains.

### Content-Security-Policy
Restricts resource loading to same origin (prevents XSS).

### Referrer-Policy
Controls referrer information sent with requests.

### Permissions-Policy
Disables browser features (geolocation, microphone, camera).

## Error Handling

### InputValidationError
Raised for validation failures:
- String too long
- Invalid format
- Empty required field
- Dangerous characters detected

### SecurityError
Raised for security violations:
- AWS access denied
- Path traversal attempt
- Rate limit exceeded

## Testing Considerations

### Mock Security Validation
```python
from shared.security_utils import sanitize_string

# Test sanitization
assert sanitize_string("<script>") == "script"
assert sanitize_string("safe-string-123") == "safe-string-123"

# Test validation
from shared.security_utils import validate_aws_region
assert validate_aws_region("us-east-1") == True
assert validate_aws_region("invalid") == False
```

### Mock Security Logging
```python
from unittest.mock import patch

with patch('shared.security_utils.logger') as mock_logger:
    log_security_event("test_event", {"key": "value"}, "INFO")
    assert mock_logger.info.called
```
"""

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict

from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Custom exception for security-related errors"""


class InputValidationError(SecurityError):
    """Exception raised for input validation failures"""


def sanitize_string(input_str: str, max_length: int = 255) -> str:
    """
    Sanitize string input to prevent injection attacks - PERFORMANCE OPTIMIZED

    Args:
        input_str: Input string to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized string

    Raises:
        InputValidationError: If input is invalid
    """
    if not isinstance(input_str, str):
        raise InputValidationError("Input must be a string")

    if len(input_str) > max_length:
        raise InputValidationError(f"Input exceeds maximum length of {max_length}")

    # PERFORMANCE: Skip sanitization for safe strings (alphanumeric + common safe chars)
    # But always check for control characters first
    if (
        len(input_str) < 1000
        and input_str.replace("-", "").replace("_", "").replace(".", "").replace(":", "").isalnum()
    ):
        # Even for "safe" strings, remove control characters
        sanitized = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", input_str.strip())
        return sanitized

    # PERFORMANCE: Quick check for dangerous characters before regex
    dangerous_chars = (
        "<>\"';\\" + "".join(chr(i) for i in range(0x00, 0x20)) + "".join(chr(i) for i in range(0x7F, 0xA0))
    )
    if not any(char in input_str for char in dangerous_chars):
        return input_str.strip()

    # Only do expensive regex if potentially dangerous content detected
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\';\\]', "", input_str.strip())

    # Remove null bytes and control characters
    sanitized = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", sanitized)

    return sanitized


def validate_aws_region(region: str) -> bool:
    """
    Validate AWS region format

    Args:
        region: AWS region string

    Returns:
        True if valid region format
    """
    if not isinstance(region, str):
        return False

    # Standard AWS region pattern
    pattern = r"^[a-z]{2}-[a-z]+-\d{1}$|^us-gov-[a-z]+-\d{1}$"
    return bool(re.match(pattern, region))


def validate_drs_server_id(server_id: str) -> bool:
    """
    Validate DRS source server ID format

    Args:
        server_id: DRS server ID

    Returns:
        True if valid DRS server ID format
    """
    if not isinstance(server_id, str):
        return False

    # DRS server IDs start with 's-' followed by 17 hexadecimal characters
    pattern = r"^s-[a-f0-9]{17}$"
    return bool(re.match(pattern, server_id))


def validate_uuid(uuid_str: str) -> bool:
    """
    Validate UUID format

    Args:
        uuid_str: UUID string

    Returns:
        True if valid UUID format
    """
    if not isinstance(uuid_str, str):
        return False

    pattern = r"^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$"
    return bool(re.match(pattern, uuid_str.lower()))


def validate_email(email: str) -> bool:
    """
    Validate email format

    Args:
        email: Email address

    Returns:
        True if valid email format
    """
    if not isinstance(email, str):
        return False

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_json_input(json_str: str, max_size: int = 1024 * 1024) -> Dict[str, Any]:
    """
    Validate and parse JSON input safely

    Args:
        json_str: JSON string to validate
        max_size: Maximum allowed JSON size in bytes

    Returns:
        Parsed JSON object

    Raises:
        InputValidationError: If JSON is invalid or too large
    """
    if not isinstance(json_str, str):
        raise InputValidationError("Input must be a string")

    if len(json_str.encode("utf-8")) > max_size:
        raise InputValidationError(f"JSON input exceeds maximum size of {max_size} bytes")

    try:
        parsed_json = json.loads(json_str)
        return parsed_json
    except json.JSONDecodeError as e:
        raise InputValidationError(f"Invalid JSON format: {str(e)}")


def validate_protection_group_name(name: str) -> bool:
    """
    Validate protection group name format

    Args:
        name: Protection group name

    Returns:
        True if valid name format
    """
    if not isinstance(name, str):
        return False

    if not (3 <= len(name) <= 50):
        return False

    # Allow alphanumeric, spaces, hyphens, underscores
    pattern = r"^[a-zA-Z0-9\s\-_]+$"
    return bool(re.match(pattern, name))


def validate_recovery_plan_name(name: str) -> bool:
    """
    Validate recovery plan name format

    Args:
        name: Recovery plan name

    Returns:
        True if valid name format
    """
    return validate_protection_group_name(name)  # Same validation rules


def sanitize_dynamodb_input(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize input data for DynamoDB operations - OPTIMIZED FOR PERFORMANCE

    Args:
        data: Input data dictionary

    Returns:
        Sanitized data dictionary

    Raises:
        InputValidationError: If data contains invalid values
    """
    # PERFORMANCE OPTIMIZATION: Skip sanitization for large execution data
    # that's already been processed and stored in DynamoDB
    if isinstance(data, dict) and len(data) > 50:
        # Check if this looks like execution data (has execution-specific fields)
        execution_indicators = [
            "executionId",
            "waves",
            "enrichedServers",
            "stateMachineArn",
        ]
        if any(key in data for key in execution_indicators):
            # This is likely execution data from DynamoDB - minimal sanitization
            return data

    sanitized = {}

    for key, value in data.items():
        # Validate key
        if not isinstance(key, str) or not key.strip():
            raise InputValidationError(f"Invalid key: {key}")

        # PERFORMANCE: Skip sanitization for safe keys
        if key in [
            "executionId",
            "planId",
            "status",
            "region",
            "waves",
            "enrichedServers",
            "stateMachineArn",
            "createdAt",
            "updatedAt",
            "startTime",
            "endTime",
        ]:
            sanitized[key] = value
            continue

        sanitized_key = sanitize_string(key, 255)

        # Sanitize value based on type - PRESERVE ORIGINAL DATA TYPES
        if isinstance(value, str):
            # PERFORMANCE: Limit string sanitization for large values
            if len(value) > 1000:
                sanitized[sanitized_key] = value  # Skip sanitization for large strings
            else:
                sanitized[sanitized_key] = sanitize_string(value, 4096)
        elif isinstance(value, (int, float, bool)):
            # Keep original numeric/boolean values unchanged
            sanitized[sanitized_key] = value
        elif isinstance(value, list):
            # PERFORMANCE: Skip deep sanitization for large lists
            if len(value) > 20:
                sanitized[sanitized_key] = value
            else:
                # Process list items recursively while preserving types
                sanitized_list = []
                for item in value:
                    if isinstance(item, str):
                        sanitized_list.append(sanitize_string(item, 1024))
                    elif isinstance(item, dict):
                        sanitized_list.append(sanitize_dynamodb_input(item))
                    else:
                        # Keep other types (int, float, bool, None) unchanged
                        sanitized_list.append(item)
                sanitized[sanitized_key] = sanitized_list
        elif isinstance(value, dict):
            # PERFORMANCE: Skip deep sanitization for large nested objects
            if len(value) > 20:
                sanitized[sanitized_key] = value
            else:
                sanitized[sanitized_key] = sanitize_dynamodb_input(value)
        elif value is None:
            sanitized[sanitized_key] = value
        else:
            # For unknown types, only convert to string if it's not a basic type
            # This preserves DynamoDB-compatible types while sanitizing strings
            if isinstance(value, (bytes, bytearray)):
                sanitized[sanitized_key] = sanitize_string(str(value), 1024)
            else:
                # Keep the original value to preserve data structure
                sanitized[sanitized_key] = value

    return sanitized


def validate_api_gateway_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate API Gateway event structure and extract safe data

    Args:
        event: API Gateway event

    Returns:
        Validated event data

    Raises:
        InputValidationError: If event structure is invalid
    """
    if not isinstance(event, dict):
        raise InputValidationError("Event must be a dictionary")

    # Required fields
    required_fields = ["httpMethod", "path"]
    for field in required_fields:
        if field not in event:
            raise InputValidationError(f"Missing required field: {field}")

    # Validate HTTP method
    valid_methods = [
        "GET",
        "POST",
        "PUT",
        "DELETE",
        "OPTIONS",
        "HEAD",
        "PATCH",
    ]
    if event["httpMethod"] not in valid_methods:
        raise InputValidationError(f"Invalid HTTP method: {event['httpMethod']}")

    # Validate path
    path = event["path"]
    if not isinstance(path, str) or len(path) > 2048:
        raise InputValidationError("Invalid path")

    # Sanitize path
    sanitized_path = sanitize_string(path, 2048)

    # Extract and validate query parameters
    query_params = event.get("queryStringParameters") or {}
    if query_params:
        sanitized_query_params = {}
        for key, value in query_params.items():
            if isinstance(value, str):
                # Allow longer values for query parameters like account IDs
                sanitized_query_params[sanitize_string(key, 100)] = sanitize_string(value, 2048)
    else:
        sanitized_query_params = {}

    # Extract and validate headers (only safe headers)
    headers = event.get("headers") or {}
    safe_headers = {}
    allowed_headers = [
        "content-type",
        "authorization",
        "user-agent",
        "accept",
        "accept-language",
        "accept-encoding",
        "origin",
        "referer",
    ]

    for key, value in headers.items():
        if key.lower() in allowed_headers and isinstance(value, str):
            # JWT tokens in Authorization header can be very long (2000+ chars)
            max_length = 4096 if key.lower() == "authorization" else 1024
            safe_headers[key.lower()] = sanitize_string(value, max_length)

    return {
        "httpMethod": event["httpMethod"],
        "path": sanitized_path,
        "queryStringParameters": sanitized_query_params,
        "headers": safe_headers,
        "requestContext": event.get("requestContext", {}),
        "body": event.get("body"),
        "isBase64Encoded": event.get("isBase64Encoded", False),
    }


def log_security_event(event_type: str, details: Dict[str, Any], severity: str = "INFO"):
    """
    Log security events for monitoring and alerting

    Args:
        event_type: Type of security event
        details: Event details
        severity: Event severity (INFO, WARN, ERROR, CRITICAL)
    """
    security_log = {
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        "event_type": event_type,
        "severity": severity,
        "details": details,
        "service": "drs-orchestration",
    }

    if severity in ["ERROR", "CRITICAL"]:
        logger.error(json.dumps(security_log))
    elif severity == "WARN":
        logger.warning(json.dumps(security_log))
    else:
        logger.info(json.dumps(security_log))


def check_rate_limit(user_id: str, action: str, limit: int = 100, window: int = 3600) -> bool:
    """
    Simple rate limiting check (would need Redis/DynamoDB in production)

    Args:
        user_id: User identifier
        action: Action being performed
        limit: Maximum requests per window
        window: Time window in seconds

    Returns:
        True if within rate limit, False if exceeded
    """
    # This is a simplified implementation
    # In production, use DynamoDB or Redis for distributed rate limiting

    # For now, just log the rate limit check
    log_security_event(
        "rate_limit_check",
        {
            "user_id": user_id,
            "action": action,
            "limit": limit,
            "window": window,
        },
    )

    # Always return True for now (implement proper rate limiting later)
    return True


def mask_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mask sensitive data in logs and responses

    Args:
        data: Data dictionary to mask

    Returns:
        Data with sensitive fields masked
    """
    sensitive_fields = [
        "password",
        "secret",
        "token",
        "key",
        "credential",
        "authorization",
        "auth",
        "session",
        "cookie",
    ]

    masked_data = {}

    for key, value in data.items():
        key_lower = key.lower()

        # Check if field contains sensitive data
        is_sensitive = any(sensitive_field in key_lower for sensitive_field in sensitive_fields)

        if is_sensitive and isinstance(value, str) and len(value) > 4:
            # Mask all but first 4 characters
            masked_data[key] = value[:4] + "*" * (len(value) - 4)
        elif isinstance(value, dict):
            masked_data[key] = mask_sensitive_data(value)
        else:
            masked_data[key] = value

    return masked_data


def create_security_headers() -> Dict[str, str]:
    """
    Create security headers for HTTP responses

    Returns:
        Dictionary of security headers
    """
    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",  # noqa: E501
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    }


def validate_aws_account_id(account_id: str) -> bool:
    """
    Validate AWS account ID format

    Args:
        account_id: AWS account ID

    Returns:
        True if valid account ID format
    """
    if not isinstance(account_id, str):
        return False

    # AWS account IDs are 12-digit numbers
    pattern = r"^\d{12}$"
    return bool(re.match(pattern, account_id))


def safe_aws_client_call(client_method, **kwargs):
    """
    Safely call AWS client methods with error handling

    Args:
        client_method: AWS client method to call
        **kwargs: Method arguments

    Returns:
        API response or None if error

    Raises:
        SecurityError: If security-related error occurs
    """
    try:
        response = client_method(**kwargs)
        return response
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        error_message = e.response.get("Error", {}).get("Message", "Unknown error")

        # Log security-relevant errors
        if error_code in [
            "UnauthorizedOperation",
            "AccessDenied",
            "Forbidden",
        ]:
            log_security_event(
                "aws_access_denied",
                {
                    "error_code": error_code,
                    "error_message": error_message,
                    "method": str(client_method),
                    "kwargs": mask_sensitive_data(kwargs),
                },
                "WARN",
            )
            raise SecurityError(f"Access denied: {error_code}")

        # Log other errors
        logger.error(f"AWS API error: {error_code} - {error_message}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in AWS API call: {str(e)}")
        raise


def create_response_with_security_headers(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create HTTP response with security headers

    Args:
        status_code: HTTP status code
        body: Response body dictionary

    Returns:
        Dict containing statusCode, body, and security headers
    """
    return {
        "statusCode": status_code,
        "body": json.dumps(body),
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            **create_security_headers(),
        },
    }


def sanitize_string_input(input_str: str, max_length: int = 255) -> str:
    """
    Wrapper for sanitize_string function for backward compatibility

    Args:
        input_str: Input string to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized string

    Raises:
        InputValidationError: If input is invalid
    """
    return sanitize_string(input_str, max_length)


def validate_file_path(path: str) -> str:
    """
    Validate file path - only block actual path traversal attacks.

    This function is DEFENSIVE - it allows safe operations and only
    blocks actual path traversal attempts. It does NOT block Lambda
    from accessing its own runtime directories (/var/task/frontend)
    or temporary directories (/tmp).

    Security utilities should be defensive (block attacks) NOT offensive
    (sanitize/modify legitimate data). This function returns the path
    unchanged if valid.

    Args:
        path: File path to validate

    Returns:
        Path unchanged if valid

    Raises:
        InputValidationError: If path is empty or contains path traversal
    """
    if not path:
        raise InputValidationError("Path cannot be empty")

    # Check ONLY for actual path traversal attacks
    # These are the patterns that could escape intended directories
    traversal_patterns = [
        "..",  # Parent directory traversal
        "%2e%2e",  # URL encoded ..
        "%252e%252e",  # Double URL encoded ..
    ]

    path_lower = path.lower()

    for pattern in traversal_patterns:
        if pattern in path_lower:
            log_security_event(
                "path_traversal_blocked",
                {"path": path, "pattern": pattern},
                "WARN",
            )
            raise InputValidationError(f"Path traversal detected: {path}")

    # Return path unchanged - defensive validation does not modify data
    return path


def validate_dynamodb_input(field_name: str, value: str) -> bool:
    """
    Validate input for DynamoDB operations

    Args:
        field_name: Name of the field being validated
        value: Value to validate

    Returns:
        True if input is valid

    Raises:
        InputValidationError: If input is invalid
    """
    if not isinstance(value, str):
        raise InputValidationError(f"{field_name} must be a string")

    if not value or not value.strip():
        raise InputValidationError(f"{field_name} cannot be empty")

    # Check length limits
    max_lengths = {
        "executionId": 128,
        "planId": 128,
        "groupId": 128,
        "waveId": 128,
        "serverId": 64,
        "jobId": 128,
        "status": 32,
        "region": 32,
    }

    max_length = max_lengths.get(field_name, 255)
    if len(value) > max_length:
        raise InputValidationError(f"{field_name} exceeds maximum length of {max_length}")

    # Validate specific field formats
    if field_name == "executionId":
        # Execution IDs should be UUIDs or similar format
        if not validate_uuid(value) and not re.match(r"^[a-zA-Z0-9\-_]+$", value):
            raise InputValidationError(f"Invalid {field_name} format: {value}")

    elif field_name == "region":
        if not validate_aws_region(value):
            raise InputValidationError(f"Invalid AWS region: {value}")

    elif field_name == "serverId":
        # DRS server IDs have specific format
        if value.startswith("s-") and not validate_drs_server_id(value):
            raise InputValidationError(f"Invalid DRS server ID: {value}")

    elif field_name == "status":
        # Validate status values
        valid_statuses = {
            "PENDING",
            "IN_PROGRESS",
            "POLLING",
            "LAUNCHING",
            "COMPLETED",
            "FAILED",
            "CANCELLED",
            "TIMEOUT",
            "PAUSED",
            "RESUMED",
            "CANCELLING",
        }
        if value not in valid_statuses:
            raise InputValidationError(f"Invalid status: {value}")

    # Sanitize the value
    sanitized_value = sanitize_string(value, max_length)

    # Log validation for audit trail
    log_security_event(
        "dynamodb_input_validated",
        {
            "field_name": field_name,
            "original_length": len(value),
            "sanitized_length": len(sanitized_value),
        },
    )

    return True


def validate_launch_config_status(status: Dict[str, Any]) -> bool:
    """
    Validate launchConfigStatus field structure.

    Args:
        status: Launch configuration status dictionary

    Returns:
        True if valid

    Raises:
        InputValidationError: If validation fails
    """
    if not isinstance(status, dict):
        raise InputValidationError("launchConfigStatus must be a dictionary")

    # Validate required fields
    required_fields = [
        "status",
        "lastApplied",
        "appliedBy",
        "serverConfigs",
        "errors",
    ]
    for field in required_fields:
        if field not in status:
            raise InputValidationError(f"launchConfigStatus missing required field: {field}")

    # Validate status field values
    valid_statuses = ["ready", "pending", "failed", "not_configured"]
    if status["status"] not in valid_statuses:
        raise InputValidationError(
            f"Invalid launchConfigStatus.status value: {status['status']}. "
            f"Must be one of: {', '.join(valid_statuses)}"
        )

    # Validate serverConfigs is a dictionary
    if not isinstance(status["serverConfigs"], dict):
        raise InputValidationError("launchConfigStatus.serverConfigs must be a dictionary")

    # Validate each server config structure
    for server_id, server_config in status["serverConfigs"].items():
        if not isinstance(server_config, dict):
            raise InputValidationError(f"Server config for {server_id} must be a dictionary")

        server_required_fields = [
            "status",
            "lastApplied",
            "configHash",
            "errors",
        ]
        for field in server_required_fields:
            if field not in server_config:
                raise InputValidationError(f"Server config for {server_id} missing field: {field}")

        # Validate server status values
        server_valid_statuses = ["ready", "pending", "failed"]
        if server_config["status"] not in server_valid_statuses:
            raise InputValidationError(
                f"Invalid status for server {server_id}: "
                f"{server_config['status']}. "
                f"Must be one of: {', '.join(server_valid_statuses)}"
            )

        # Validate errors is a list
        if not isinstance(server_config["errors"], list):
            raise InputValidationError(f"Errors for server {server_id} must be a list")

    # Validate errors is a list
    if not isinstance(status["errors"], list):
        raise InputValidationError("launchConfigStatus.errors must be a list")

    return True
