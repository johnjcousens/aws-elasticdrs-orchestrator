"""
Property-based tests for calculate_config_hash().

Feature: async-launch-config-sync, Property 25: ConfigHash Determinism

For any launch configuration, calculate_config_hash should produce
the same hash on repeated calls, ensuring reliable drift detection.

Validates: Requirements 11.5
"""

import os
import sys

import pytest  # noqa: F401
from hypothesis import given, settings, strategies as st

# Add lambda directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda"))

from shared.launch_config_service import calculate_config_hash  # noqa: E402


# ---------------------------------------------------------------------------
# Strategies for generating launch configuration values
# ---------------------------------------------------------------------------

def _instance_type() -> st.SearchStrategy:
    """Generate valid AWS instance type strings."""
    return st.sampled_from(["t3.micro", "t3.small", "t3.medium", "m5.large", "c5.xlarge", "r5.2xlarge"])


def _subnet_id() -> st.SearchStrategy:
    """Generate valid subnet IDs."""
    return st.from_regex(r"subnet-[a-f0-9]{8,17}", fullmatch=True)


def _security_group_ids() -> st.SearchStrategy:
    """Generate lists of valid security group IDs."""
    return st.lists(st.from_regex(r"sg-[a-f0-9]{8,17}", fullmatch=True), min_size=0, max_size=5)


def _instance_profile_name() -> st.SearchStrategy:
    """Generate valid IAM instance profile names."""
    return st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_", min_size=1, max_size=20)


def _private_ipv4() -> st.SearchStrategy:
    """Generate valid private IPv4 addresses."""
    return st.one_of(
        st.tuples(
            st.just(10),
            st.integers(min_value=0, max_value=255),
            st.integers(min_value=0, max_value=255),
            st.integers(min_value=0, max_value=255),
        ),
        st.tuples(
            st.just(172),
            st.integers(min_value=16, max_value=31),
            st.integers(min_value=0, max_value=255),
            st.integers(min_value=0, max_value=255),
        ),
        st.tuples(
            st.just(192),
            st.just(168),
            st.integers(min_value=0, max_value=255),
            st.integers(min_value=0, max_value=255),
        ),
    ).map(lambda t: f"{t[0]}.{t[1]}.{t[2]}.{t[3]}")


# ===========================================================================
# Property tests for ConfigHash Determinism
# Feature: async-launch-config-sync, Property 25: ConfigHash Determinism
# ===========================================================================


class TestConfigHashDeterminism:
    """Property tests for calculate_config_hash determinism."""

    @settings(max_examples=100)
    @given(
        instance_type=_instance_type(),
        subnet_id=_subnet_id(),
        sg_ids=_security_group_ids(),
    )
    def test_same_input_produces_same_hash(self, instance_type: str, subnet_id: str, sg_ids: list) -> None:
        """
        Feature: async-launch-config-sync, Property 25: ConfigHash Determinism
        Validates: Requirements 11.5

        For any launch configuration, calculate_config_hash should produce
        the same hash on repeated calls.
        """
        config = {
            "instanceType": instance_type,
            "subnetId": subnet_id,
            "securityGroupIds": sg_ids,
        }

        hash1 = calculate_config_hash(config)
        hash2 = calculate_config_hash(config)

        assert hash1 == hash2, f"Hash changed between calls: {hash1} != {hash2}"
        assert hash1.startswith("sha256:"), f"Hash format incorrect: {hash1}"

    @settings(max_examples=100)
    @given(
        instance_type=_instance_type(),
        subnet_id=_subnet_id(),
        sg_ids=_security_group_ids(),
        copy_private_ip=st.booleans(),
        copy_tags=st.booleans(),
    )
    def test_hash_format_always_valid(self, instance_type: str, subnet_id: str, sg_ids: list, copy_private_ip: bool,
                                      copy_tags: bool) -> None:
        """
        Feature: async-launch-config-sync, Property 25: ConfigHash Determinism
        Validates: Requirements 11.5

        For any launch configuration, the hash format should always be "sha256:...".
        """
        config = {
            "instanceType": instance_type,
            "subnetId": subnet_id,
            "securityGroupIds": sg_ids,
            "copyPrivateIp": copy_private_ip,
            "copyTags": copy_tags,
        }

        config_hash = calculate_config_hash(config)

        assert config_hash.startswith("sha256:"), f"Hash format incorrect: {config_hash}"
        assert len(config_hash) == 71, f"Hash length incorrect: {len(config_hash)} (expected 71 = 'sha256:' + 64 hex)"
        # Verify hex characters after prefix
        hex_part = config_hash[7:]
        assert all(c in "0123456789abcdef" for c in hex_part), f"Hash contains non-hex characters: {hex_part}"

    @settings(max_examples=100)
    @given(
        instance_type1=_instance_type(),
        instance_type2=_instance_type(),
        subnet_id=_subnet_id(),
        sg_ids=_security_group_ids(),
    )
    def test_different_inputs_produce_different_hashes(self, instance_type1: str, instance_type2: str, subnet_id: str,
                                                       sg_ids: list) -> None:
        """
        Feature: async-launch-config-sync, Property 25: ConfigHash Determinism
        Validates: Requirements 11.5

        For different launch configurations, calculate_config_hash should
        produce different hashes (collision resistance).
        """
        # Only test when instance types are actually different
        if instance_type1 == instance_type2:
            return

        config1 = {
            "instanceType": instance_type1,
            "subnetId": subnet_id,
            "securityGroupIds": sg_ids,
        }

        config2 = {
            "instanceType": instance_type2,
            "subnetId": subnet_id,
            "securityGroupIds": sg_ids,
        }

        hash1 = calculate_config_hash(config1)
        hash2 = calculate_config_hash(config2)

        assert hash1 != hash2, f"Different configs produced same hash: {config1} vs {config2}"

    @settings(max_examples=100)
    @given(
        instance_type=_instance_type(),
        subnet_id=_subnet_id(),
        sg_ids=_security_group_ids(),
    )
    def test_security_group_order_affects_hash(self, instance_type: str, subnet_id: str, sg_ids: list) -> None:
        """
        Feature: async-launch-config-sync, Property 25: ConfigHash Determinism
        Validates: Requirements 11.5

        Security group IDs order matters for hash calculation. Different orders
        produce different hashes, which is expected behavior since json.dumps
        only sorts top-level keys, not nested lists.
        """
        # Only test when we have multiple unique security groups
        if len(sg_ids) < 2 or len(set(sg_ids)) < 2:
            return

        config1 = {
            "instanceType": instance_type,
            "subnetId": subnet_id,
            "securityGroupIds": sg_ids,
        }

        # Reverse the security group order
        config2 = {
            "instanceType": instance_type,
            "subnetId": subnet_id,
            "securityGroupIds": list(reversed(sg_ids)),
        }

        hash1 = calculate_config_hash(config1)
        hash2 = calculate_config_hash(config2)

        # Different order produces different hash (expected behavior)
        if sg_ids != list(reversed(sg_ids)):
            assert hash1 != hash2, f"Different SG order produced same hash: {sg_ids}"

    @settings(max_examples=100)
    @given(
        instance_type=_instance_type(),
        subnet_id=_subnet_id(),
        sg_ids=_security_group_ids(),
        instance_profile=_instance_profile_name(),
        static_ip=_private_ipv4(),
        copy_private_ip=st.booleans(),
        copy_tags=st.booleans(),
        launch_disposition=st.sampled_from(["STARTED", "STOPPED"]),
        right_sizing=st.sampled_from(["NONE", "BASIC"]),
    )
    def test_comprehensive_config_determinism(self, instance_type: str, subnet_id: str, sg_ids: list,
                                              instance_profile: str, static_ip: str, copy_private_ip: bool,
                                              copy_tags: bool, launch_disposition: str, right_sizing: str) -> None:
        """
        Feature: async-launch-config-sync, Property 25: ConfigHash Determinism
        Validates: Requirements 11.5

        For comprehensive launch configurations with all fields, hash should
        remain deterministic across multiple calls.
        """
        config = {
            "instanceType": instance_type,
            "subnetId": subnet_id,
            "securityGroupIds": sg_ids,
            "instanceProfileName": instance_profile,
            "staticPrivateIp": static_ip,
            "copyPrivateIp": copy_private_ip,
            "copyTags": copy_tags,
            "launchDisposition": launch_disposition,
            "targetInstanceTypeRightSizingMethod": right_sizing,
        }

        hash1 = calculate_config_hash(config)
        hash2 = calculate_config_hash(config)
        hash3 = calculate_config_hash(config)

        assert hash1 == hash2 == hash3, f"Hash not deterministic: {hash1}, {hash2}, {hash3}"
        assert hash1.startswith("sha256:"), f"Hash format incorrect: {hash1}"

    @settings(max_examples=100)
    @given(config=st.dictionaries(st.text(min_size=1, max_size=20), st.one_of(st.text(), st.integers(), st.booleans(),
                                                                                st.lists(st.text(), max_size=3))))
    def test_arbitrary_config_determinism(self, config: dict) -> None:
        """
        Feature: async-launch-config-sync, Property 25: ConfigHash Determinism
        Validates: Requirements 11.5

        For any arbitrary configuration dictionary, hash calculation should
        be deterministic and never raise exceptions.
        """
        hash1 = calculate_config_hash(config)
        hash2 = calculate_config_hash(config)

        assert hash1 == hash2, f"Hash not deterministic for arbitrary config: {config}"
        assert hash1.startswith("sha256:"), f"Hash format incorrect: {hash1}"

    @settings(max_examples=100)
    @given(st.just(None))
    def test_empty_config_produces_consistent_hash(self, _) -> None:
        """
        Feature: async-launch-config-sync, Property 25: ConfigHash Determinism
        Validates: Requirements 11.5

        Empty configuration should produce a consistent "sha256:empty" hash.
        """
        hash1 = calculate_config_hash({})
        hash2 = calculate_config_hash({})
        hash3 = calculate_config_hash(None)

        assert hash1 == "sha256:empty", f"Empty config hash incorrect: {hash1}"
        assert hash2 == "sha256:empty", f"Empty config hash incorrect: {hash2}"
        assert hash3 == "sha256:empty", f"None config hash incorrect: {hash3}"
        assert hash1 == hash2 == hash3, "Empty config hashes not consistent"
