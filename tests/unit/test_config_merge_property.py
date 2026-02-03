"""
Property-based tests for configuration merge correctness.

Feature: per-server-launch-template-customization
Property 1: Configuration Merge Correctness

For any protection group with group defaults and per-server overrides,
the effective configuration should equal group defaults with server
overrides taking precedence.

Validates: Requirements 6.1, 6.2, 6.5
"""

import pytest  # noqa: F401
from hypothesis import given, strategies as st  # noqa: E402
import sys  # noqa: E402
import os  # noqa: E402

# Add lambda directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda"))

from shared.config_merge import get_effective_launch_config  # noqa: E402


# Strategy for generating launch config fields
launch_config_fields = st.sampled_from(
    [
        "subnetId",
        "securityGroupIds",
        "instanceType",
        "instanceProfileName",
        "staticPrivateIp",
        "associatePublicIp",
        "monitoring",
        "ebsOptimized",
    ]
)


@given(
    group_defaults=st.dictionaries(
        keys=launch_config_fields,
        values=st.one_of(
            st.text(min_size=1, max_size=50),
            st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=5),
            st.booleans(),
        ),
        min_size=1,
        max_size=5,
    ),
    server_overrides=st.dictionaries(
        keys=launch_config_fields,
        values=st.one_of(
            st.text(min_size=1, max_size=50),
            st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=5),
            st.booleans(),
        ),
        min_size=0,
        max_size=3,
    ),
    use_group_defaults=st.booleans(),
)
def test_configuration_merge_correctness(
    group_defaults, server_overrides, use_group_defaults
):
    """
    Property 1: Configuration Merge Correctness

    For any protection group with group defaults and per-server overrides,
    the effective configuration should equal group defaults with server
    overrides taking precedence.
    """
    # Arrange
    protection_group = {
        "launchConfig": group_defaults,
        "servers": [
            {
                "sourceServerId": "s-test",
                "useGroupDefaults": use_group_defaults,
                "launchTemplate": server_overrides,
            }
        ],
    }

    # Act
    effective = get_effective_launch_config(protection_group, "s-test")

    # Assert
    if use_group_defaults:
        # Partial override: group defaults + server overrides
        for key, value in group_defaults.items():
            if key not in server_overrides or server_overrides[key] is None:
                assert effective.get(key) == value, (
                    f"Field {key} should inherit group default {value}, "
                    f"got {effective.get(key)}"
                )

        for key, value in server_overrides.items():
            if value is not None:
                assert effective.get(key) == value, (
                    f"Field {key} should use server override {value}, "
                    f"got {effective.get(key)}"
                )
    else:
        # Full override: only server config
        for key, value in server_overrides.items():
            if value is not None:
                assert effective.get(key) == value, (
                    f"Field {key} should use server override {value}, "
                    f"got {effective.get(key)}"
                )


@given(
    group_defaults=st.dictionaries(
        keys=launch_config_fields,
        values=st.text(min_size=1, max_size=50),
        min_size=2,
        max_size=5,
    )
)
def test_no_server_config_returns_group_defaults(group_defaults):
    """
    Property 1 (Edge Case): No Server Config

    When a server has no custom configuration, the effective config
    should exactly match the group defaults.
    """
    # Arrange
    protection_group = {"launchConfig": group_defaults, "servers": []}

    # Act
    effective = get_effective_launch_config(protection_group, "s-nonexistent")

    # Assert
    assert effective == group_defaults, (
        f"Expected group defaults {group_defaults}, got {effective}"
    )


@given(
    group_defaults=st.dictionaries(
        keys=launch_config_fields,
        values=st.text(min_size=1, max_size=50),
        min_size=2,
        max_size=5,
    ),
    server_overrides=st.dictionaries(
        keys=launch_config_fields,
        values=st.text(min_size=1, max_size=50),
        min_size=1,
        max_size=3,
    ),
)
def test_merge_idempotence(group_defaults, server_overrides):
    """
    Property 12: Configuration Merge Idempotence

    Applying the same per-server configuration twice should result in
    the same effective configuration as applying it once.
    """
    # Arrange
    protection_group = {
        "launchConfig": group_defaults,
        "servers": [
            {
                "sourceServerId": "s-test",
                "useGroupDefaults": True,
                "launchTemplate": server_overrides,
            }
        ],
    }

    # Act
    effective1 = get_effective_launch_config(protection_group, "s-test")
    effective2 = get_effective_launch_config(protection_group, "s-test")

    # Assert
    assert effective1 == effective2, (
        f"Merge should be idempotent: {effective1} != {effective2}"
    )


def test_configuration_merge_specific_examples():
    """Unit test examples for configuration merge"""
    # Example 1: Partial override with useGroupDefaults=True
    pg = {
        "launchConfig": {
            "subnetId": "subnet-group",
            "instanceType": "c6a.large",
            "securityGroupIds": ["sg-group"],
        },
        "servers": [
            {
                "sourceServerId": "s-1",
                "useGroupDefaults": True,
                "launchTemplate": {
                    "staticPrivateIp": "10.0.1.100",
                    "instanceType": "c6a.xlarge",
                },
            }
        ],
    }

    effective = get_effective_launch_config(pg, "s-1")
    assert effective["subnetId"] == "subnet-group"  # Inherited
    assert effective["instanceType"] == "c6a.xlarge"  # Overridden
    assert effective["securityGroupIds"] == ["sg-group"]  # Inherited
    assert effective["staticPrivateIp"] == "10.0.1.100"  # Server-specific

    # Example 2: Full override with useGroupDefaults=False
    pg2 = {
        "launchConfig": {
            "subnetId": "subnet-group",
            "instanceType": "c6a.large",
        },
        "servers": [
            {
                "sourceServerId": "s-2",
                "useGroupDefaults": False,
                "launchTemplate": {
                    "subnetId": "subnet-custom",
                    "instanceType": "c6a.2xlarge",
                },
            }
        ],
    }

    effective2 = get_effective_launch_config(pg2, "s-2")
    assert effective2["subnetId"] == "subnet-custom"
    assert effective2["instanceType"] == "c6a.2xlarge"
    # Group defaults should not be present
    assert len(effective2) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
