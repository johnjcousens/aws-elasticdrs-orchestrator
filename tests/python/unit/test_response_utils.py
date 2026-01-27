"""
Unit tests for response_utils shared utilities.

Tests API Gateway response generation and JSON encoding.
"""

import json
import os
import sys
from decimal import Decimal

import pytest

# Add lambda directory to path for imports
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "lambda"
    ),
)

from shared.response_utils import DecimalEncoder, response


def test_decimal_encoder_whole_number():
    """Test DecimalEncoder converts whole number Decimal to int"""
    data = {"count": Decimal("42")}
    result = json.dumps(data, cls=DecimalEncoder)
    assert result == '{"count": 42}'
    assert isinstance(json.loads(result)["count"], int)


def test_decimal_encoder_float():
    """Test DecimalEncoder converts decimal Decimal to float"""
    data = {"price": Decimal("19.99")}
    result = json.dumps(data, cls=DecimalEncoder)
    assert result == '{"price": 19.99}'
    assert isinstance(json.loads(result)["price"], float)


def test_decimal_encoder_nested():
    """Test DecimalEncoder handles nested Decimal values"""
    data = {
        "item": {
            "quantity": Decimal("5"),
            "price": Decimal("12.50"),
        },
        "total": Decimal("62.50"),
    }
    result = json.dumps(data, cls=DecimalEncoder)
    parsed = json.loads(result)
    assert parsed["item"]["quantity"] == 5
    assert parsed["item"]["price"] == 12.50
    assert parsed["total"] == 62.50


def test_decimal_encoder_list():
    """Test DecimalEncoder handles lists with Decimal values"""
    data = {"values": [Decimal("1"), Decimal("2.5"), Decimal("3")]}
    result = json.dumps(data, cls=DecimalEncoder)
    parsed = json.loads(result)
    assert parsed["values"] == [1, 2.5, 3]


def test_response_basic():
    """Test response generates basic API Gateway response"""
    result = response(200, {"message": "success"})

    assert result["statusCode"] == 200
    assert "headers" in result
    assert "body" in result

    body = json.loads(result["body"])
    assert body["message"] == "success"


def test_response_cors_headers():
    """Test response includes CORS headers"""
    result = response(200, {"data": "test"})

    headers = result["headers"]
    assert headers["Access-Control-Allow-Origin"] == "*"
    assert "Content-Type,Authorization" in headers["Access-Control-Allow-Headers"]
    assert "GET,POST,PUT,DELETE,OPTIONS" in headers["Access-Control-Allow-Methods"]


def test_response_security_headers():
    """Test response includes security headers"""
    result = response(200, {"data": "test"})

    headers = result["headers"]
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "DENY"


def test_response_custom_headers():
    """Test response merges custom headers"""
    custom_headers = {
        "X-Custom-Header": "custom-value",
        "Cache-Control": "no-cache",
    }

    result = response(200, {"data": "test"}, headers=custom_headers)

    headers = result["headers"]
    assert headers["X-Custom-Header"] == "custom-value"
    assert headers["Cache-Control"] == "no-cache"
    # Default headers should still be present
    assert headers["Content-Type"] == "application/json"
    assert headers["Access-Control-Allow-Origin"] == "*"


def test_response_custom_headers_override():
    """Test custom headers can override default headers"""
    custom_headers = {
        "Content-Type": "text/plain",
    }

    result = response(200, {"data": "test"}, headers=custom_headers)

    headers = result["headers"]
    assert headers["Content-Type"] == "text/plain"


def test_response_error_status():
    """Test response with error status codes"""
    result = response(404, {"error": "Not Found"})

    assert result["statusCode"] == 404
    body = json.loads(result["body"])
    assert body["error"] == "Not Found"


def test_response_with_decimal_values():
    """Test response handles Decimal values in body"""
    body_data = {
        "count": Decimal("10"),
        "price": Decimal("99.99"),
    }

    result = response(200, body_data)

    body = json.loads(result["body"])
    assert body["count"] == 10
    assert body["price"] == 99.99


def test_response_with_complex_body():
    """Test response handles complex nested body"""
    body_data = {
        "items": [
            {"id": Decimal("1"), "name": "Item 1", "price": Decimal("10.50")},
            {"id": Decimal("2"), "name": "Item 2", "price": Decimal("20.99")},
        ],
        "total": Decimal("31.49"),
        "metadata": {
            "count": Decimal("2"),
            "currency": "USD",
        },
    }

    result = response(200, body_data)

    body = json.loads(result["body"])
    assert len(body["items"]) == 2
    assert body["items"][0]["id"] == 1
    assert body["items"][0]["price"] == 10.50
    assert body["total"] == 31.49
    assert body["metadata"]["count"] == 2


def test_response_empty_body():
    """Test response with empty body"""
    result = response(204, {})

    assert result["statusCode"] == 204
    body = json.loads(result["body"])
    assert body == {}


def test_response_list_body():
    """Test response with list as body"""
    body_data = [
        {"id": Decimal("1"), "name": "Item 1"},
        {"id": Decimal("2"), "name": "Item 2"},
    ]

    result = response(200, body_data)

    body = json.loads(result["body"])
    assert isinstance(body, list)
    assert len(body) == 2
    assert body[0]["id"] == 1
