# Security Sanitization Tests

## Overview

This directory contains comprehensive tests for security utilities to ensure they properly sanitize malicious inputs while preserving legitimate data.

## Test Files

### test_security_utils.py
**36 tests** - Core security utility functions
- String sanitization
- Input validation (AWS regions, DRS server IDs, UUIDs, emails)
- JSON validation
- Protection group/recovery plan name validation
- AWS account ID validation
- DynamoDB input sanitization
- API Gateway event validation
- Sensitive data masking
- Security headers

### test_security_sanitization_edge_cases.py
**48 tests** - Edge cases and real-world data patterns

#### Test Categories

**1. Legitimate Inputs Not Broken (20 tests)**
Ensures security functions don't break valid AWS and application data:
- ✅ AWS ARNs preserved
- ✅ AWS resource IDs preserved (DRS, EC2, VPC)
- ✅ IP addresses preserved (IPv4, IPv6)
- ✅ CIDR blocks preserved
- ✅ DNS names preserved
- ✅ Email addresses preserved
- ✅ URLs preserved
- ✅ ISO 8601 timestamps preserved
- ✅ UUIDs preserved
- ✅ Base64 encoded data preserved
- ✅ AWS tags preserved
- ✅ File paths preserved
- ✅ Version numbers preserved
- ✅ AWS region names preserved
- ✅ Numeric strings preserved
- ✅ Alphanumeric with hyphens/underscores preserved

**2. DynamoDB Input Preservation (6 tests)**
Ensures data types and structures remain intact:
- ✅ Execution data structure preserved
- ✅ Numeric types remain as numbers (not converted to strings)
- ✅ Boolean types remain as booleans
- ✅ None values remain as None
- ✅ Nested structures preserved
- ✅ Large lists/objects pass through without deep sanitization

**3. Malicious Inputs Blocked (6 tests)**
Ensures security functions properly sanitize attacks:
- ✅ XSS attempts sanitized
- ✅ SQL injection attempts sanitized
- ✅ Command injection attempts sanitized
- ✅ Path traversal attempts blocked
- ✅ Null byte injection sanitized
- ✅ Control characters removed

**4. Edge Cases and Boundaries (8 tests)**
Tests boundary conditions and special cases:
- ✅ Empty strings handled
- ✅ Whitespace-only strings trimmed
- ✅ Max length boundaries respected
- ✅ Exceeds max length rejected
- ✅ Unicode characters preserved
- ✅ Mixed safe/dangerous chars partially sanitized
- ✅ Performance optimization for safe strings
- ✅ Performance optimization for large safe strings

**5. Real-World Data Patterns (8 tests)**
Tests actual data from DRS operations:
- ✅ DRS job IDs preserved
- ✅ CloudFormation stack names preserved
- ✅ Lambda function names preserved
- ✅ DynamoDB table names preserved
- ✅ S3 bucket names preserved
- ✅ API Gateway paths preserved
- ✅ Cognito User Pool IDs preserved
- ✅ Step Functions execution ARNs preserved
- ✅ JWT token structure preserved

## Why These Tests Matter

### Problem Statement
Security sanitization functions must walk a fine line:
- **Too aggressive**: Break legitimate inputs (AWS ARNs, resource IDs, JSON data)
- **Too lenient**: Allow malicious inputs (XSS, SQL injection, command injection)

### Solution
Comprehensive test coverage ensures:
1. **Legitimate data passes through unchanged** - No data corruption
2. **Malicious data is sanitized** - Security maintained
3. **Performance optimizations work** - Fast path for safe strings
4. **Data types preserved** - Numbers stay numbers, booleans stay booleans
5. **Real-world patterns validated** - Actual AWS resource formats tested

## Running Tests

### Run all security tests
```bash
pytest tests/python/unit/test_security_utils.py -v
pytest tests/python/unit/test_security_sanitization_edge_cases.py -v
```

### Run specific test class
```bash
pytest tests/python/unit/test_security_sanitization_edge_cases.py::TestLegitimateInputsNotBroken -v
```

### Run specific test
```bash
pytest tests/python/unit/test_security_sanitization_edge_cases.py::TestLegitimateInputsNotBroken::test_aws_arns_preserved -v
```

### Run with coverage
```bash
pytest tests/python/unit/test_security_*.py --cov=lambda/shared/security_utils --cov-report=term-missing
```

## Test Results

**Total Tests**: 84 (36 + 48)
**Status**: ✅ All passing
**Coverage**: Security utilities comprehensively tested
**Performance**: Tests complete in < 0.1 seconds

## Key Findings

### What Works Well
1. **AWS resource IDs** - All AWS resource formats pass through unchanged
2. **Data type preservation** - Numbers, booleans, None values preserved
3. **Performance optimization** - Fast path for alphanumeric strings works correctly
4. **Malicious input blocking** - XSS, SQL injection, command injection properly sanitized

### What to Watch
1. **JWT tokens** - Quotes in JWT payloads would be removed (but headers/signatures preserved)
2. **JSON strings** - Use `validate_json_input()` instead of `sanitize_string()` for JSON
3. **Large data** - Performance optimization skips deep sanitization for large objects (>20 keys, >20 items)

## Maintenance

### When to Update Tests
- Adding new security sanitization functions
- Modifying existing sanitization logic
- Discovering new AWS resource ID formats
- Finding edge cases in production
- Performance optimization changes

### Test Coverage Goals
- ✅ All security utility functions tested
- ✅ All AWS resource ID formats tested
- ✅ All malicious input patterns tested
- ✅ All data type preservation tested
- ✅ All edge cases tested

## Related Documentation

- [Security Utils Source](../../../lambda/shared/security_utils.py)
- [CamelCase Validation Tests](README_CAMELCASE_VALIDATION.md)
- [RBAC Tests](test_rbac_enforcement.py)
- [RBAC Middleware Tests](test_rbac_middleware.py)
- [API Handler Tests](test_api_handler.py)
