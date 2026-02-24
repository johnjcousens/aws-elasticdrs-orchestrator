"""
Unit tests for validate_launch_config_formats() function.

Tests format-only validation of launch configuration fields
without AWS API calls.

Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5
"""

import os
import sys

import pytest

# Add lambda directory to path for imports
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "../../lambda")
)
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "../../lambda/shared")
)

from shared.launch_config_validation import (
    validate_launch_config_formats,
)


class TestValidateLaunchConfigFormats:
    """Tests for validate_launch_config_formats()."""

    def test_empty_config_is_valid(self):
        """Empty config has no fields to validate."""
        result = validate_launch_config_formats({})
        assert result["valid"] is True
        assert result["errors"] == []

    def test_all_valid_fields(self):
        """Config with all valid fields passes."""
        config = {
            "staticPrivateIp": "10.0.1.50",
            "subnetId": "subnet-0abcdef1234567890",
            "securityGroupIds": ["sg-0abcdef1234567890"],
            "instanceType": "t3.micro",
        }
        result = validate_launch_config_formats(config)
        assert result["valid"] is True
        assert result["errors"] == []

    # --- staticPrivateIp tests ---

    def test_valid_private_ip(self):
        """Valid private IPv4 address passes."""
        result = validate_launch_config_formats(
            {"staticPrivateIp": "192.168.1.100"}
        )
        assert result["valid"] is True

    def test_invalid_ip_format(self):
        """Non-IPv4 string is rejected."""
        result = validate_launch_config_formats(
            {"staticPrivateIp": "not-an-ip"}
        )
        assert result["valid"] is False
        assert len(result["errors"]) == 1
        assert result["errors"][0]["field"] == "staticPrivateIp"

    def test_ip_out_of_range(self):
        """IPv4 with octets > 255 is rejected."""
        result = validate_launch_config_formats(
            {"staticPrivateIp": "999.999.999.999"}
        )
        assert result["valid"] is False
        assert result["errors"][0]["field"] == "staticPrivateIp"

    def test_public_ip_rejected(self):
        """Public IP address is rejected."""
        result = validate_launch_config_formats(
            {"staticPrivateIp": "8.8.8.8"}
        )
        assert result["valid"] is False
        assert result["errors"][0]["field"] == "staticPrivateIp"

    # --- subnetId tests ---

    def test_valid_subnet_id(self):
        """Valid subnet ID passes."""
        result = validate_launch_config_formats(
            {"subnetId": "subnet-0abcdef12"}
        )
        assert result["valid"] is True

    def test_valid_subnet_id_17_hex(self):
        """Subnet ID with 17 hex chars passes."""
        result = validate_launch_config_formats(
            {"subnetId": "subnet-0abcdef1234567890"}
        )
        assert result["valid"] is True

    def test_invalid_subnet_id_format(self):
        """Invalid subnet ID format is rejected."""
        result = validate_launch_config_formats(
            {"subnetId": "invalid-subnet"}
        )
        assert result["valid"] is False
        assert result["errors"][0]["field"] == "subnetId"

    def test_subnet_id_too_short(self):
        """Subnet ID with < 8 hex chars is rejected."""
        result = validate_launch_config_formats(
            {"subnetId": "subnet-0abc"}
        )
        assert result["valid"] is False
        assert result["errors"][0]["field"] == "subnetId"

    def test_subnet_id_uppercase_rejected(self):
        """Subnet ID with uppercase hex is rejected."""
        result = validate_launch_config_formats(
            {"subnetId": "subnet-0ABCDEF12"}
        )
        assert result["valid"] is False
        assert result["errors"][0]["field"] == "subnetId"

    # --- securityGroupIds tests ---

    def test_valid_security_group_ids(self):
        """Valid security group IDs pass."""
        result = validate_launch_config_formats(
            {"securityGroupIds": [
                "sg-0abcdef12",
                "sg-0abcdef1234567890",
            ]}
        )
        assert result["valid"] is True

    def test_invalid_security_group_id(self):
        """Invalid security group ID is rejected."""
        result = validate_launch_config_formats(
            {"securityGroupIds": ["sg-invalid"]}
        )
        assert result["valid"] is False
        assert result["errors"][0]["field"] == "securityGroupIds"

    def test_security_group_ids_not_list(self):
        """Non-list securityGroupIds is rejected."""
        result = validate_launch_config_formats(
            {"securityGroupIds": "sg-0abcdef12"}
        )
        assert result["valid"] is False
        assert result["errors"][0]["field"] == "securityGroupIds"
        assert "must be a list" in result["errors"][0]["message"]

    def test_empty_security_group_list_valid(self):
        """Empty security group list passes."""
        result = validate_launch_config_formats(
            {"securityGroupIds": []}
        )
        assert result["valid"] is True

    def test_mixed_valid_invalid_sg_ids(self):
        """Mix of valid and invalid SG IDs reports errors."""
        result = validate_launch_config_formats(
            {"securityGroupIds": [
                "sg-0abcdef12",
                "bad-sg",
            ]}
        )
        assert result["valid"] is False
        assert len(result["errors"]) == 1

    # --- instanceType tests ---

    def test_valid_instance_type(self):
        """Valid instance type passes."""
        result = validate_launch_config_formats(
            {"instanceType": "t3.micro"}
        )
        assert result["valid"] is True

    def test_valid_instance_type_complex(self):
        """Complex instance type like c6a.2xlarge passes."""
        result = validate_launch_config_formats(
            {"instanceType": "c6a.2xlarge"}
        )
        assert result["valid"] is True

    def test_invalid_instance_type(self):
        """Invalid instance type format is rejected."""
        result = validate_launch_config_formats(
            {"instanceType": "not-a-type"}
        )
        assert result["valid"] is False
        assert result["errors"][0]["field"] == "instanceType"

    def test_instance_type_no_dot(self):
        """Instance type without dot is rejected."""
        result = validate_launch_config_formats(
            {"instanceType": "t3micro"}
        )
        assert result["valid"] is False
        assert result["errors"][0]["field"] == "instanceType"

    # --- Multiple errors ---

    def test_multiple_invalid_fields(self):
        """Multiple invalid fields produce multiple errors."""
        config = {
            "staticPrivateIp": "bad-ip",
            "subnetId": "bad-subnet",
            "securityGroupIds": ["bad-sg"],
            "instanceType": "bad",
        }
        result = validate_launch_config_formats(config)
        assert result["valid"] is False
        assert len(result["errors"]) == 4

    def test_unrelated_fields_ignored(self):
        """Fields not in the validation set are ignored."""
        config = {
            "copyPrivateIp": True,
            "copyTags": True,
            "launchDisposition": "STARTED",
        }
        result = validate_launch_config_formats(config)
        assert result["valid"] is True
        assert result["errors"] == []

    def test_none_fields_skipped(self):
        """None-valued fields are skipped."""
        config = {
            "staticPrivateIp": None,
            "subnetId": None,
            "securityGroupIds": None,
            "instanceType": None,
        }
        result = validate_launch_config_formats(config)
        assert result["valid"] is True
        assert result["errors"] == []
