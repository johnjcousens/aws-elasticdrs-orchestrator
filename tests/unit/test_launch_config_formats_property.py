"""
Property-based tests for validate_launch_config_formats().

Feature: async-launch-config-sync, Property 23: Input Format Validation

For any launch configuration input, format validation should accept
only correctly formatted values and reject everything else, consistently.

Validates: Requirements 10.2, 10.3, 10.4, 10.5
"""

import os
import re
import sys

import pytest  # noqa: F401
from hypothesis import given, settings, strategies as st

# Add lambda directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda"))

from shared.launch_config_validation import validate_launch_config_formats  # noqa: E402


# ---------------------------------------------------------------------------
# Strategies for generating valid values
# ---------------------------------------------------------------------------

def _private_ipv4() -> st.SearchStrategy:
    """Generate valid private IPv4 addresses (10.x, 172.16-31.x, 192.168.x)."""
    return st.one_of(
        # 10.0.0.0/8
        st.tuples(
            st.just(10),
            st.integers(min_value=0, max_value=255),
            st.integers(min_value=0, max_value=255),
            st.integers(min_value=0, max_value=255),
        ),
        # 172.16.0.0/12
        st.tuples(
            st.just(172),
            st.integers(min_value=16, max_value=31),
            st.integers(min_value=0, max_value=255),
            st.integers(min_value=0, max_value=255),
        ),
        # 192.168.0.0/16
        st.tuples(
            st.just(192),
            st.just(168),
            st.integers(min_value=0, max_value=255),
            st.integers(min_value=0, max_value=255),
        ),
    ).map(lambda t: f"{t[0]}.{t[1]}.{t[2]}.{t[3]}")


def _valid_hex_id(prefix: str) -> st.SearchStrategy:
    """Generate valid AWS resource IDs like subnet-<8-17 hex> or sg-<8-17 hex>."""
    return st.integers(min_value=8, max_value=17).flatmap(
        lambda length: st.text(
            alphabet="0123456789abcdef", min_size=length, max_size=length
        ).map(lambda h: f"{prefix}{h}")
    )


def _valid_instance_type() -> st.SearchStrategy:
    """Generate valid AWS instance type strings like t3.micro, c6a.2xlarge."""
    family = st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=4)
    gen = st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789", min_size=0, max_size=3)
    size = st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789", min_size=1, max_size=6)
    return st.tuples(family, gen, size).map(lambda t: f"{t[0]}{t[1]}.{t[2]}")


# ---------------------------------------------------------------------------
# Regex patterns (must match the implementation)
# ---------------------------------------------------------------------------

SUBNET_PATTERN = re.compile(r"^subnet-[0-9a-f]{8,17}$")
SG_PATTERN = re.compile(r"^sg-[0-9a-f]{8,17}$")
INSTANCE_TYPE_PATTERN = re.compile(r"^[a-z][a-z0-9]*\.[a-z0-9]+$")


# ===========================================================================
# Property tests for staticPrivateIp
# Feature: async-launch-config-sync, Property 23: Input Format Validation
# ===========================================================================


class TestStaticPrivateIpProperty:
    """Property tests for staticPrivateIp validation."""

    @settings(max_examples=100)
    @given(ip=_private_ipv4())
    def test_valid_private_ips_always_accepted(self, ip: str) -> None:
        """
        Feature: async-launch-config-sync, Property 23: Input Format Validation
        Validates: Requirements 10.2

        For any valid private IPv4 address, validation should accept it.
        """
        result = validate_launch_config_formats({"staticPrivateIp": ip})
        assert result["valid"] is True, f"Valid private IP {ip} was rejected"
        assert result["errors"] == []

    @settings(max_examples=100)
    @given(text=st.text(min_size=1, max_size=30))
    def test_random_strings_handled_consistently(self, text: str) -> None:
        """
        Feature: async-launch-config-sync, Property 23: Input Format Validation
        Validates: Requirements 10.2

        For any random string, IP validation should only accept valid
        private IPv4 addresses. The function must never raise an exception.
        """
        import ipaddress

        result = validate_launch_config_formats({"staticPrivateIp": text})

        try:
            ip_obj = ipaddress.IPv4Address(text)
            is_valid_private = ip_obj.is_private
        except (ValueError, ipaddress.AddressValueError):
            is_valid_private = False

        if is_valid_private:
            assert result["valid"] is True, f"Valid private IP {text} was rejected"
        else:
            assert result["valid"] is False, f"Invalid IP {text!r} was accepted"
            assert any(e["field"] == "staticPrivateIp" for e in result["errors"])

    @settings(max_examples=100)
    @given(
        a=st.integers(min_value=0, max_value=255),
        b=st.integers(min_value=0, max_value=255),
        c=st.integers(min_value=0, max_value=255),
        d=st.integers(min_value=0, max_value=255),
    )
    def test_public_ips_rejected(self, a: int, b: int, c: int, d: int) -> None:
        """
        Feature: async-launch-config-sync, Property 23: Input Format Validation
        Validates: Requirements 10.2

        For any valid IPv4 that is NOT private, validation should reject it.
        """
        import ipaddress

        ip = f"{a}.{b}.{c}.{d}"
        ip_obj = ipaddress.IPv4Address(ip)

        if not ip_obj.is_private:
            result = validate_launch_config_formats({"staticPrivateIp": ip})
            assert result["valid"] is False, f"Public IP {ip} was accepted"
            assert any(e["field"] == "staticPrivateIp" for e in result["errors"])


# ===========================================================================
# Property tests for subnetId
# Feature: async-launch-config-sync, Property 23: Input Format Validation
# ===========================================================================


class TestSubnetIdProperty:
    """Property tests for subnetId validation."""

    @settings(max_examples=100)
    @given(subnet_id=_valid_hex_id("subnet-"))
    def test_valid_subnet_ids_always_accepted(self, subnet_id: str) -> None:
        """
        Feature: async-launch-config-sync, Property 23: Input Format Validation
        Validates: Requirements 10.3

        For any string matching subnet-[0-9a-f]{8,17}, validation should accept it.
        """
        result = validate_launch_config_formats({"subnetId": subnet_id})
        assert result["valid"] is True, f"Valid subnet ID {subnet_id} was rejected"
        assert result["errors"] == []

    @settings(max_examples=100)
    @given(text=st.text(min_size=1, max_size=30))
    def test_random_strings_handled_consistently(self, text: str) -> None:
        """
        Feature: async-launch-config-sync, Property 23: Input Format Validation
        Validates: Requirements 10.3

        For any random string, subnetId validation should only accept
        strings matching the subnet-[0-9a-f]{8,17} pattern.
        """
        result = validate_launch_config_formats({"subnetId": text})

        if SUBNET_PATTERN.match(text):
            assert result["valid"] is True, f"Valid subnet {text} was rejected"
        else:
            assert result["valid"] is False, f"Invalid subnet {text!r} was accepted"
            assert any(e["field"] == "subnetId" for e in result["errors"])


# ===========================================================================
# Property tests for securityGroupIds
# Feature: async-launch-config-sync, Property 23: Input Format Validation
# ===========================================================================


class TestSecurityGroupIdsProperty:
    """Property tests for securityGroupIds validation."""

    @settings(max_examples=100)
    @given(sg_ids=st.lists(_valid_hex_id("sg-"), min_size=1, max_size=5))
    def test_valid_sg_ids_always_accepted(self, sg_ids: list) -> None:
        """
        Feature: async-launch-config-sync, Property 23: Input Format Validation
        Validates: Requirements 10.4

        For any list of valid sg-[0-9a-f]{8,17} IDs, validation should accept.
        """
        result = validate_launch_config_formats({"securityGroupIds": sg_ids})
        assert result["valid"] is True, f"Valid SG IDs {sg_ids} were rejected"
        assert result["errors"] == []

    @settings(max_examples=100)
    @given(sg_ids=st.lists(st.text(min_size=1, max_size=25), min_size=1, max_size=5))
    def test_random_sg_ids_handled_consistently(self, sg_ids: list) -> None:
        """
        Feature: async-launch-config-sync, Property 23: Input Format Validation
        Validates: Requirements 10.4

        For any list of random strings, only lists where every element
        matches sg-[0-9a-f]{8,17} should pass validation.
        """
        result = validate_launch_config_formats({"securityGroupIds": sg_ids})

        all_valid = all(SG_PATTERN.match(sg) for sg in sg_ids)
        if all_valid:
            assert result["valid"] is True
        else:
            assert result["valid"] is False
            assert any(e["field"] == "securityGroupIds" for e in result["errors"])

    @settings(max_examples=100)
    @given(non_list=st.one_of(st.text(min_size=1), st.integers(), st.booleans()))
    def test_non_list_always_rejected(self, non_list) -> None:
        """
        Feature: async-launch-config-sync, Property 23: Input Format Validation
        Validates: Requirements 10.4

        securityGroupIds must be a list; any non-list value should be rejected.
        """
        result = validate_launch_config_formats({"securityGroupIds": non_list})
        assert result["valid"] is False
        assert any("must be a list" in e["message"] for e in result["errors"])


# ===========================================================================
# Property tests for instanceType
# Feature: async-launch-config-sync, Property 23: Input Format Validation
# ===========================================================================


class TestInstanceTypeProperty:
    """Property tests for instanceType validation."""

    @settings(max_examples=100)
    @given(instance_type=_valid_instance_type())
    def test_valid_instance_types_always_accepted(self, instance_type: str) -> None:
        """
        Feature: async-launch-config-sync, Property 23: Input Format Validation
        Validates: Requirements 10.5

        For any string matching [a-z][a-z0-9]*\\.[a-z0-9]+, validation should accept.
        """
        result = validate_launch_config_formats({"instanceType": instance_type})
        assert result["valid"] is True, f"Valid instance type {instance_type} was rejected"
        assert result["errors"] == []

    @settings(max_examples=100)
    @given(text=st.text(min_size=1, max_size=20))
    def test_random_strings_handled_consistently(self, text: str) -> None:
        """
        Feature: async-launch-config-sync, Property 23: Input Format Validation
        Validates: Requirements 10.5

        For any random string, instanceType validation should only accept
        strings matching the AWS instance type pattern.
        """
        result = validate_launch_config_formats({"instanceType": text})

        if INSTANCE_TYPE_PATTERN.match(text):
            assert result["valid"] is True, f"Valid type {text} was rejected"
        else:
            assert result["valid"] is False, f"Invalid type {text!r} was accepted"
            assert any(e["field"] == "instanceType" for e in result["errors"])


# ===========================================================================
# Consistency property: same input always produces same output
# Feature: async-launch-config-sync, Property 23: Input Format Validation
# ===========================================================================


class TestConsistencyProperty:
    """Validation is deterministic — same input always gives same result."""

    @settings(max_examples=100)
    @given(
        ip=st.one_of(st.none(), st.text(min_size=0, max_size=20)),
        subnet=st.one_of(st.none(), st.text(min_size=0, max_size=30)),
        sgs=st.one_of(st.none(), st.lists(st.text(min_size=0, max_size=25), max_size=3)),
        itype=st.one_of(st.none(), st.text(min_size=0, max_size=20)),
    )
    def test_deterministic_output(self, ip, subnet, sgs, itype) -> None:
        """
        Feature: async-launch-config-sync, Property 23: Input Format Validation
        Validates: Requirements 10.2, 10.3, 10.4, 10.5

        For any combination of inputs, calling validate_launch_config_formats
        twice with the same config must produce identical results.
        """
        config = {}
        if ip is not None:
            config["staticPrivateIp"] = ip
        if subnet is not None:
            config["subnetId"] = subnet
        if sgs is not None:
            config["securityGroupIds"] = sgs
        if itype is not None:
            config["instanceType"] = itype

        result1 = validate_launch_config_formats(config)
        result2 = validate_launch_config_formats(config)

        assert result1["valid"] == result2["valid"]
        assert result1["errors"] == result2["errors"]
