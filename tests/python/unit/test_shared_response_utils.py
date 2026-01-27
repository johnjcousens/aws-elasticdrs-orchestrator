"""
Unit tests for Shared Response Utilities

Tests the shared response formatting functions used by all decomposed handlers.
"""

import json
import os
import sys
from decimal import Decimal

import pytest

# Set AWS region BEFORE any boto3 imports
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

# Add lambda directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "lambda"))

from shared.response_utils import response, DecimalEncoder


class TestResponseFunction:
    """Test response formatting function."""

    def test_success_response(self):
        """Should format success response correctly."""
        result = response(200, {"message": "success"})
        assert result["statusCode"] == 200
        assert "application/json" in result["headers"]["Content-Type"]
        body = json.loads(result["body"])
        assert body["message"] == "success"

    def test_error_response(self):
        """Should format error response correctly."""
        result = response(400, {"error": "Bad Request"})
        assert result["statusCode"] == 400
        body = json.loads(result["body"])
        assert body["error"] == "Bad Request"

    def test_includes_cors_headers(self):
        """Should include CORS headers."""
        result = response(200, {})
        assert "Access-Control-Allow-Origin" in result["headers"]
        assert result["headers"]["Access-Control-Allow-Origin"] == "*"

    def test_includes_security_headers(self):
        """Should include security headers."""
        result = response(200, {})
        headers = result["headers"]
        assert "X-Content-Type-Options" in headers
        assert headers["X-Content-Type-Options"] == "nosniff"
        assert "X-Frame-Options" in headers
        assert headers["X-Frame-Options"] == "DENY"

    def test_handles_decimal_values(self):
        """Should handle Decimal values in response body."""
        result = response(200, {"count": Decimal("42"), "price": Decimal("19.99")})
        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["count"] == 42
        assert body["price"] == 19.99


class TestDecimalEncoder:
    """Test DecimalEncoder for DynamoDB Decimal handling."""

    def test_encodes_decimal_as_int(self):
        """Should encode Decimal without fractional part as int."""
        data = {"count": Decimal("42")}
        result = json.dumps(data, cls=DecimalEncoder)
        assert result == '{"count": 42}'

    def test_encodes_decimal_as_float(self):
        """Should encode Decimal with fractional part as float."""
        data = {"price": Decimal("19.99")}
        result = json.dumps(data, cls=DecimalEncoder)
        assert result == '{"price": 19.99}'

    def test_encodes_nested_decimals(self):
        """Should encode nested Decimal values."""
        data = {
            "item": {
                "count": Decimal("10"),
                "price": Decimal("5.50"),
                "items": [Decimal("1"), Decimal("2.5")]
            }
        }
        result = json.dumps(data, cls=DecimalEncoder)
        parsed = json.loads(result)
        assert parsed["item"]["count"] == 10
        assert parsed["item"]["price"] == 5.5
        assert parsed["item"]["items"] == [1, 2.5]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
