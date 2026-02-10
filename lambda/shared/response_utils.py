"""
Response Utilities for API Gateway and Direct Lambda Invocation

Provides standardized response generation for both API Gateway and direct
Lambda invocation modes with CORS, security headers, error handling, and
DynamoDB Decimal serialization. Ensures consistent response format across
all endpoints and invocation patterns.

## Integration Points

### 1. API Gateway Mode (Existing Functionality)
```python
from shared.response_utils import response

def lambda_handler(event, context):
    # Success response
    return response(200, {
        "message": "Success",
        "data": {"executionId": "exec-123"}
    })

    # Error response
    return response(400, {
        "error": "Invalid input",
        "details": "Missing required field: planId"
    })
```

### 2. Direct Invocation Mode (New Functionality)
```python
from shared.response_utils import (
    success_response,
    error_response,
    ERROR_MISSING_PARAMETER,
    ERROR_NOT_FOUND
)

def handle_direct_invocation(event, context):
    operation = event.get("operation")

    if not operation:
        return error_response(
            ERROR_MISSING_PARAMETER,
            "operation parameter is required",
            details={"parameter": "operation"}
        )

    if operation == "get_item":
        item_id = event.get("itemId")
        if not item_id:
            return error_response(
                ERROR_MISSING_PARAMETER,
                "itemId parameter is required",
                details={"parameter": "itemId"}
            )

        item = get_item_from_db(item_id)
        if not item:
            return error_response(
                ERROR_NOT_FOUND,
                f"Item {item_id} not found",
                details={"itemId": item_id}
            )

        return success_response({"item": item})
```

### 3. Dual Mode Support (API Gateway + Direct)
```python
from shared.response_utils import (
    response,
    success_response,
    error_response,
    format_api_gateway_response,
    ERROR_INVALID_INVOCATION
)

def lambda_handler(event, context):
    # Detect invocation mode
    if "requestContext" in event:
        # API Gateway mode
        return handle_api_gateway(event, context)
    elif "operation" in event:
        # Direct invocation mode
        result = handle_direct_invocation(event, context)
        # Result is already in correct format for direct mode
        return result
    else:
        # Invalid invocation
        error = error_response(
            ERROR_INVALID_INVOCATION,
            "Event must contain 'requestContext' or 'operation'"
        )
        # Wrap in API Gateway format if needed
        return format_api_gateway_response(error, status_code=400)
```

### 4. Error Responses with Retry Guidance
```python
from shared.response_utils import (
    error_response,
    ERROR_DRS_ERROR,
    ERROR_DYNAMODB_ERROR
)

# Transient error with retry guidance
try:
    result = drs_client.describe_source_servers()
except ClientError as e:
    if e.response["Error"]["Code"] == "ServiceUnavailable":
        return error_response(
            ERROR_DRS_ERROR,
            "DRS service temporarily unavailable",
            details={"awsError": e.response["Error"]["Code"]},
            retryable=True,
            retry_after=30
        )

# DynamoDB throttling error
try:
    table.put_item(Item=item)
except ClientError as e:
    if e.response["Error"]["Code"] == "ProvisionedThroughputExceededException":
        return error_response(
            ERROR_DYNAMODB_ERROR,
            "DynamoDB capacity exceeded",
            details={"table": table_name},
            retryable=True,
            retry_after=5
        )
```

## Error Code Constants

### Invocation Errors
- `ERROR_INVALID_INVOCATION`: Invalid event format
- `ERROR_INVALID_OPERATION`: Unsupported operation name

### Validation Errors
- `ERROR_MISSING_PARAMETER`: Required parameter missing
- `ERROR_INVALID_PARAMETER`: Parameter value invalid

### Authorization Errors
- `ERROR_AUTHORIZATION_FAILED`: IAM principal not authorized

### Resource Errors
- `ERROR_NOT_FOUND`: Resource does not exist
- `ERROR_ALREADY_EXISTS`: Resource already exists
- `ERROR_INVALID_STATE`: Resource in invalid state

### AWS Service Errors (Retryable)
- `ERROR_DYNAMODB_ERROR`: DynamoDB operation failed
- `ERROR_DRS_ERROR`: DRS API operation failed
- `ERROR_STEP_FUNCTIONS_ERROR`: Step Functions operation failed
- `ERROR_STS_ERROR`: STS assume role failed
- `ERROR_INTERNAL_ERROR`: Unexpected internal error

## Response Formats

### Direct Invocation Success Response
```json
{
  "executionId": "exec-123",
  "status": "RUNNING",
  "startTime": "2025-01-31T10:00:00Z"
}
```

### Direct Invocation Error Response
```json
{
  "error": "MISSING_PARAMETER",
  "message": "Required parameter is missing",
  "details": {
    "parameter": "groupId"
  }
}
```

### Direct Invocation Error with Retry Guidance
```json
{
  "error": "DRS_ERROR",
  "message": "DRS service temporarily unavailable",
  "retryable": true,
  "retryAfter": 30
}
```

### API Gateway Response (Wrapped)
```json
{
  "statusCode": 200,
  "headers": {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY"
  },
  "body": "{\"executionId\":\"exec-123\"}"
}
```

## DynamoDB Decimal Handling (Automatic)
```python
from shared.response_utils import success_response
from decimal import Decimal

# DynamoDB returns Decimal types
dynamodb_item = {
    "executionId": "exec-123",
    "waveCount": Decimal("5"),      # Whole number
    "duration": Decimal("123.45")   # Decimal number
}

# DecimalEncoder automatically converts:
# - Decimal("5") → 5 (int)
# - Decimal("123.45") → 123.45 (float)
result = success_response(dynamodb_item)
# Result: {"executionId": "exec-123", "waveCount": 5, "duration": 123.45}
```

## Security Headers

### X-Content-Type-Options: nosniff
Prevents browsers from MIME-sniffing responses away from declared
content-type. Protects against drive-by download attacks.

### X-Frame-Options: DENY
Prevents page from being displayed in iframe/frame/embed/object.
Protects against clickjacking attacks.

## CORS Configuration

### Allowed Origins
- `*` (all origins) - suitable for internal APIs behind authentication
- For production, consider restricting to specific domains

### Allowed Methods
- GET, POST, PUT, DELETE, OPTIONS

### Allowed Headers
- Content-Type, Authorization
"""

import json
from decimal import Decimal
from typing import Any, Dict, Optional


# Error code constants for standardized error responses
ERROR_INVALID_INVOCATION = "INVALID_INVOCATION"
ERROR_INVALID_OPERATION = "INVALID_OPERATION"
ERROR_MISSING_PARAMETER = "MISSING_PARAMETER"
ERROR_INVALID_PARAMETER = "INVALID_PARAMETER"
ERROR_AUTHORIZATION_FAILED = "AUTHORIZATION_FAILED"
ERROR_NOT_FOUND = "NOT_FOUND"
ERROR_ALREADY_EXISTS = "ALREADY_EXISTS"
ERROR_INVALID_STATE = "INVALID_STATE"
ERROR_DYNAMODB_ERROR = "DYNAMODB_ERROR"
ERROR_DRS_ERROR = "DRS_ERROR"
ERROR_STEP_FUNCTIONS_ERROR = "STEP_FUNCTIONS_ERROR"
ERROR_STS_ERROR = "STS_ERROR"
ERROR_INTERNAL_ERROR = "INTERNAL_ERROR"

# Retryable error codes (transient failures)
RETRYABLE_ERRORS = {
    ERROR_DYNAMODB_ERROR,
    ERROR_DRS_ERROR,
    ERROR_STEP_FUNCTIONS_ERROR,
    ERROR_STS_ERROR,
    ERROR_INTERNAL_ERROR,
}


class DecimalEncoder(json.JSONEncoder):
    """
    JSON encoder for DynamoDB Decimal types.

    DynamoDB stores numbers as Decimal to preserve precision. This encoder converts
    Decimal to int (if whole number) or float for JSON serialization in API responses.

    Conversion Rules:
    - Whole numbers: Decimal("5") → 5 (int)
    - Decimal numbers: Decimal("123.45") → 123.45 (float)

    Usage:
        >>> import json
        >>> from decimal import Decimal
        >>> data = {"count": Decimal("10"), "price": Decimal("19.99")}
        >>> json.dumps(data, cls=DecimalEncoder)
        '{"count": 10, "price": 19.99}'
    """

    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super(DecimalEncoder, self).default(obj)


def response(status_code: int, body: Any, headers: Optional[Dict] = None) -> Dict:
    """
    Generate API Gateway response with CORS and security headers.

    Provides standardized response format for all Lambda functions with:
    - CORS headers for cross-origin requests
    - Security headers to prevent common web vulnerabilities
    - JSON serialization with DynamoDB Decimal support

    Args:
        status_code: HTTP status code (200, 400, 403, 404, 500, etc.)
        body: Response body (dict, list, or any JSON-serializable object)
        headers: Optional custom headers to merge with defaults

    Returns:
        API Gateway response dict with statusCode, headers, and body

    Security Headers:
        - X-Content-Type-Options: nosniff (prevents MIME type sniffing)
        - X-Frame-Options: DENY (prevents clickjacking)

    Example:
        >>> response(200, {"message": "Success"})
        {
            "statusCode": 200,
            "headers": {...},
            "body": '{"message": "Success"}'
        }

        >>> response(400, {"error": "Invalid input"}, headers={"Cache-Control": "no-cache"})
        {
            "statusCode": 400,
            "headers": {..., "Cache-Control": "no-cache"},
            "body": '{"error": "Invalid input"}'
        }
    """
    default_headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,Authorization",
        "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
        # Security headers
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
    }
    if headers:
        default_headers.update(headers)

    return {
        "statusCode": status_code,
        "headers": default_headers,
        "body": json.dumps(body, cls=DecimalEncoder),
    }


def error_response(
    error_code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    retryable: Optional[bool] = None,
    retry_after: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Generate standardized error response for direct Lambda invocations.

    Creates consistent error structure with error code, human-readable
    message, optional details, and retry guidance for transient errors.

    Args:
        error_code: Error code constant (e.g., ERROR_INVALID_PARAMETER)
        message: Human-readable error message
        details: Optional dict with additional error context
        retryable: Whether error is retryable (auto-detected if None)
        retry_after: Seconds to wait before retry (for retryable errors)

    Returns:
        Dict with error, message, and optional details/retry fields

    Error Structure:
        {
            "error": "ERROR_CODE",
            "message": "Human-readable message",
            "details": {...},  # Optional
            "retryable": true,  # Optional, for transient errors
            "retryAfter": 30  # Optional, seconds to wait
        }

    Example:
        >>> error_response(
        ...     ERROR_MISSING_PARAMETER,
        ...     "Required parameter is missing",
        ...     details={"parameter": "groupId"}
        ... )
        {
            "error": "MISSING_PARAMETER",
            "message": "Required parameter is missing",
            "details": {"parameter": "groupId"}
        }

        >>> error_response(
        ...     ERROR_DRS_ERROR,
        ...     "DRS service temporarily unavailable",
        ...     retryable=True,
        ...     retry_after=30
        ... )
        {
            "error": "DRS_ERROR",
            "message": "DRS service temporarily unavailable",
            "retryable": true,
            "retryAfter": 30
        }
    """
    error_dict = {"error": error_code, "message": message}

    if details is not None:
        error_dict["details"] = details

    # Auto-detect retryable if not specified
    if retryable is None:
        retryable = error_code in RETRYABLE_ERRORS

    if retryable:
        error_dict["retryable"] = True
        if retry_after is not None:
            error_dict["retryAfter"] = retry_after

    return error_dict


def success_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate standardized success response for direct Lambda invocations.

    Returns data directly without API Gateway wrapping. Data is serialized
    with DynamoDB Decimal support.

    Args:
        data: Response data dict

    Returns:
        Dict with response data (Decimals converted to int/float)

    Example:
        >>> success_response({"executionId": "exec-123", "status": "RUNNING"})
        {"executionId": "exec-123", "status": "RUNNING"}

        >>> from decimal import Decimal
        >>> success_response({"count": Decimal("5"), "price": Decimal("19.99")})
        {"count": 5, "price": 19.99}
    """
    # Serialize and deserialize to handle Decimal conversion
    return json.loads(json.dumps(data, cls=DecimalEncoder))


def format_api_gateway_response(data: Dict[str, Any], status_code: int = 200) -> Dict[str, Any]:
    """
    Wrap response data in API Gateway format.

    Converts direct invocation response to API Gateway format with
    statusCode, headers, and JSON body.

    Args:
        data: Response data dict (can contain error or success data)
        status_code: HTTP status code (default: 200)

    Returns:
        API Gateway response dict with statusCode, headers, and body

    Example:
        >>> format_api_gateway_response({"message": "Success"})
        {
            "statusCode": 200,
            "headers": {...},
            "body": '{"message": "Success"}'
        }

        >>> format_api_gateway_response(
        ...     {"error": "NOT_FOUND", "message": "Resource not found"},
        ...     status_code=404
        ... )
        {
            "statusCode": 404,
            "headers": {...},
            "body": '{"error": "NOT_FOUND", "message": "Resource not found"}'
        }
    """
    return response(status_code, data)
