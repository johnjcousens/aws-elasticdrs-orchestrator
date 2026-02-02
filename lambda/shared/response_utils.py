"""
API Gateway Response Utilities

Provides standardized API Gateway response generation with CORS, security headers,
and DynamoDB Decimal serialization. Ensures consistent response format across all endpoints.

## Integration Points

### 1. Lambda Handler Responses (Primary Use Case)
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

    # With custom headers
    return response(200, {"data": "value"}, headers={
        "Cache-Control": "max-age=3600"
    })
```

### 2. DynamoDB Decimal Handling (Automatic)
```python
from shared.response_utils import response

# DynamoDB returns Decimal types
dynamodb_item = {
    "executionId": "exec-123",
    "waveCount": Decimal("5"),      # Whole number
    "duration": Decimal("123.45")   # Decimal number
}

# DecimalEncoder automatically converts:
# - Decimal("5") → 5 (int)
# - Decimal("123.45") → 123.45 (float)
return response(200, dynamodb_item)
# Body: {"executionId": "exec-123", "waveCount": 5, "duration": 123.45}
```

### 3. Error Responses (Consistent Format)
```python
from shared.response_utils import response

# 400 Bad Request
return response(400, {
    "error": "VALIDATION_ERROR",
    "message": "Invalid recovery plan configuration",
    "details": {"field": "waves", "issue": "Must have at least 1 wave"}
})

# 403 Forbidden
return response(403, {
    "error": "FORBIDDEN",
    "message": "Insufficient permissions",
    "required": "START_RECOVERY"
})

# 404 Not Found
return response(404, {
    "error": "NOT_FOUND",
    "message": "Recovery plan not found",
    "planId": "plan-123"
})

# 500 Internal Server Error
return response(500, {
    "error": "INTERNAL_ERROR",
    "message": "Failed to execute recovery plan",
    "details": str(exception)
})
```

## Response Format

### Standard Structure
```json
{
  "statusCode": 200,
  "headers": {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY"
  },
  "body": "{\"message\":\"Success\"}"
}
```

## Security Headers

### X-Content-Type-Options: nosniff
Prevents browsers from MIME-sniffing responses away from declared content-type.
Protects against drive-by download attacks.

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

## Decimal Encoding

### Why DecimalEncoder?
DynamoDB stores numbers as Decimal type to preserve precision.
Standard json.dumps() cannot serialize Decimal objects.

### Conversion Rules
- Whole numbers (Decimal("5")) → int (5)
- Decimal numbers (Decimal("123.45")) → float (123.45)

### Example
```python
from decimal import Decimal
import json
from shared.response_utils import DecimalEncoder

data = {
    "count": Decimal("10"),
    "price": Decimal("19.99"),
    "ratio": Decimal("0.333333")
}

# Standard json.dumps fails
json.dumps(data)  # TypeError: Object of type Decimal is not JSON serializable

# DecimalEncoder handles it
json.dumps(data, cls=DecimalEncoder)  # '{"count": 10, "price": 19.99, "ratio": 0.333333}'
```

## Testing Considerations

### Mock API Gateway Response
```python
from shared.response_utils import response

result = response(200, {"message": "test"})

assert result["statusCode"] == 200
assert "Access-Control-Allow-Origin" in result["headers"]
assert json.loads(result["body"])["message"] == "test"
```

### Test Decimal Encoding
```python
from decimal import Decimal
from shared.response_utils import response
import json

result = response(200, {"count": Decimal("5")})
body = json.loads(result["body"])
assert body["count"] == 5
assert isinstance(body["count"], int)
```
"""

import json
from decimal import Decimal
from typing import Any, Dict, Optional


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
