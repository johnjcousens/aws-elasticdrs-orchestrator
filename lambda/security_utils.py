"""
Security utilities for AWS DRS Orchestration
Provides input validation, sanitization, and security helpers
"""

import re
import json
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Custom exception for security-related errors"""
    pass


class InputValidationError(SecurityError):
    """Exception raised for input validation failures"""
    pass


def sanitize_string(input_str: str, max_length: int = 255) -> str:
    """
    Sanitize string input to prevent injection attacks
    
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
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\';\\]', '', input_str.strip())
    
    # Remove null bytes and control characters
    sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', sanitized)
    
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
    pattern = r'^[a-z]{2}-[a-z]+-\d{1}$|^us-gov-[a-z]+-\d{1}$'
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
    pattern = r'^s-[a-f0-9]{17}$'
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
    
    pattern = r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$'
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
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
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
    
    if len(json_str.encode('utf-8')) > max_size:
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
    pattern = r'^[a-zA-Z0-9\s\-_]+$'
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
    Sanitize input data for DynamoDB operations
    
    Args:
        data: Input data dictionary
        
    Returns:
        Sanitized data dictionary
        
    Raises:
        InputValidationError: If data contains invalid values
    """
    sanitized = {}
    
    for key, value in data.items():
        # Validate key
        if not isinstance(key, str) or not key.strip():
            raise InputValidationError(f"Invalid key: {key}")
        
        sanitized_key = sanitize_string(key, 255)
        
        # Sanitize value based on type
        if isinstance(value, str):
            sanitized[sanitized_key] = sanitize_string(value, 4096)
        elif isinstance(value, (int, float, bool)):
            sanitized[sanitized_key] = value
        elif isinstance(value, list):
            sanitized[sanitized_key] = [
                sanitize_string(str(item), 1024) if isinstance(item, str) else item
                for item in value
            ]
        elif isinstance(value, dict):
            sanitized[sanitized_key] = sanitize_dynamodb_input(value)
        elif value is None:
            sanitized[sanitized_key] = value
        else:
            # Convert other types to string and sanitize
            sanitized[sanitized_key] = sanitize_string(str(value), 1024)
    
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
    required_fields = ['httpMethod', 'path']
    for field in required_fields:
        if field not in event:
            raise InputValidationError(f"Missing required field: {field}")
    
    # Validate HTTP method
    valid_methods = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'HEAD', 'PATCH']
    if event['httpMethod'] not in valid_methods:
        raise InputValidationError(f"Invalid HTTP method: {event['httpMethod']}")
    
    # Validate path
    path = event['path']
    if not isinstance(path, str) or len(path) > 2048:
        raise InputValidationError("Invalid path")
    
    # Sanitize path
    sanitized_path = sanitize_string(path, 2048)
    
    # Extract and validate query parameters
    query_params = event.get('queryStringParameters') or {}
    if query_params:
        sanitized_query_params = {}
        for key, value in query_params.items():
            if isinstance(value, str):
                sanitized_query_params[sanitize_string(key, 100)] = sanitize_string(value, 1024)
    else:
        sanitized_query_params = {}
    
    # Extract and validate headers (only safe headers)
    headers = event.get('headers') or {}
    safe_headers = {}
    allowed_headers = [
        'content-type', 'authorization', 'user-agent', 'accept',
        'accept-language', 'accept-encoding', 'origin', 'referer'
    ]
    
    for key, value in headers.items():
        if key.lower() in allowed_headers and isinstance(value, str):
            safe_headers[key.lower()] = sanitize_string(value, 1024)
    
    return {
        'httpMethod': event['httpMethod'],
        'path': sanitized_path,
        'queryStringParameters': sanitized_query_params,
        'headers': safe_headers,
        'requestContext': event.get('requestContext', {}),
        'body': event.get('body'),
        'isBase64Encoded': event.get('isBase64Encoded', False)
    }


def log_security_event(event_type: str, details: Dict[str, Any], severity: str = 'INFO'):
    """
    Log security events for monitoring and alerting
    
    Args:
        event_type: Type of security event
        details: Event details
        severity: Event severity (INFO, WARN, ERROR, CRITICAL)
    """
    security_log = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'event_type': event_type,
        'severity': severity,
        'details': details,
        'service': 'drs-orchestration'
    }
    
    if severity in ['ERROR', 'CRITICAL']:
        logger.error(json.dumps(security_log))
    elif severity == 'WARN':
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
        'rate_limit_check',
        {
            'user_id': user_id,
            'action': action,
            'limit': limit,
            'window': window
        }
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
        'password', 'secret', 'token', 'key', 'credential',
        'authorization', 'auth', 'session', 'cookie'
    ]
    
    masked_data = {}
    
    for key, value in data.items():
        key_lower = key.lower()
        
        # Check if field contains sensitive data
        is_sensitive = any(sensitive_field in key_lower for sensitive_field in sensitive_fields)
        
        if is_sensitive and isinstance(value, str) and len(value) > 4:
            # Mask all but first 4 characters
            masked_data[key] = value[:4] + '*' * (len(value) - 4)
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
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'geolocation=(), microphone=(), camera=()'
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
    pattern = r'^\d{12}$'
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
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        error_message = e.response.get('Error', {}).get('Message', 'Unknown error')
        
        # Log security-relevant errors
        if error_code in ['UnauthorizedOperation', 'AccessDenied', 'Forbidden']:
            log_security_event(
                'aws_access_denied',
                {
                    'error_code': error_code,
                    'error_message': error_message,
                    'method': str(client_method),
                    'kwargs': mask_sensitive_data(kwargs)
                },
                'WARN'
            )
            raise SecurityError(f"Access denied: {error_code}")
        
        # Log other errors
        logger.error(f"AWS API error: {error_code} - {error_message}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in AWS API call: {str(e)}")
        raise