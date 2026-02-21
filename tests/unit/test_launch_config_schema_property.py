"""
Property-based tests for launch configuration schema validation.

Tests Property 4: Configuration Status Schema Validity
For any protection group with configuration status, the status field must be
one of ["ready", "pending", "failed", "not_configured"], and if status is not
"not_configured", the lastApplied timestamp must be present and valid.

Validates: Requirements 2.1, 2.2, 2.3
"""

import os
import sys
from datetime import datetime, timezone

from hypothesis import given, strategies as st
import pytest


# Add lambda directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda"))
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "../../lambda/shared")
)


# Valid status values
VALID_STATUSES = ["ready", "pending", "failed", "not_configured"]


# Strategy for generating valid ISO 8601 timestamps
@st.composite
def iso_timestamp(draw):
    """Generate valid ISO 8601 timestamp strings."""
    dt = draw(
        st.datetimes(
            min_value=datetime(2020, 1, 1),  # Naive datetime
            max_value=datetime(2030, 12, 31),  # Naive datetime
        )
    )
    # Add UTC timezone and convert to ISO format
    dt_utc = dt.replace(tzinfo=timezone.utc)
    return dt_utc.isoformat()


# Strategy for generating valid launchConfigStatus objects
@st.composite
def launch_config_status(draw):
    """Generate valid launchConfigStatus objects."""
    status_value = draw(st.sampled_from(VALID_STATUSES))
    
    # If status is not_configured, lastApplied and appliedBy should be None
    if status_value == "not_configured":
        last_applied = None
        applied_by = None
    else:
        # For other statuses, lastApplied must be present
        last_applied = draw(iso_timestamp())
        applied_by = draw(
            st.one_of(
                st.none(),
                st.text(
                    alphabet=st.characters(
                        whitelist_categories=("Lu", "Ll", "Nd"),
                        whitelist_characters="@.-_"
                    ),
                    min_size=5,
                    max_size=100
                )
            )
        )
    
    # Generate server configs
    num_servers = draw(st.integers(min_value=0, max_value=10))
    server_configs = {}
    for i in range(num_servers):
        server_id = f"s-{draw(st.text(alphabet='0123456789abcdef', min_size=17, max_size=17))}"
        server_status = draw(st.sampled_from(["ready", "pending", "failed"]))
        server_configs[server_id] = {
            "status": server_status,
            "lastApplied": draw(st.one_of(st.none(), iso_timestamp())),
            "configHash": draw(
                st.one_of(
                    st.none(),
                    st.text(min_size=10, max_size=100).map(
                        lambda x: f"sha256:{x}"
                    )
                )
            ),
            "errors": draw(
                st.lists(
                    st.text(min_size=1, max_size=200),
                    min_size=0,
                    max_size=5
                )
            )
        }
    
    # Generate errors list
    errors = draw(
        st.lists(
            st.text(min_size=1, max_size=200),
            min_size=0,
            max_size=5
        )
    )
    
    return {
        "status": status_value,
        "lastApplied": last_applied,
        "appliedBy": applied_by,
        "serverConfigs": server_configs,
        "errors": errors
    }


class TestProperty4StatusSchemaValidity:
    """
    Property 4: Configuration Status Schema Validity
    
    For any protection group with configuration status, the status field
    must be one of ["ready", "pending", "failed", "not_configured"], and
    if status is not "not_configured", the lastApplied timestamp must be
    present and valid.
    
    Validates: Requirements 2.1, 2.2, 2.3
    """

    @given(status=launch_config_status())
    def test_property_4_status_field_is_valid(self, status):
        """
        Feature: launch-config-preapplication, Property 4
        
        For any launchConfigStatus object, the status field must be one of
        the valid values: ready, pending, failed, not_configured.
        """
        # Verify status is one of the valid values
        assert status["status"] in VALID_STATUSES, (
            f"Status '{status['status']}' is not in valid statuses: "
            f"{VALID_STATUSES}"
        )

    @given(status=launch_config_status())
    def test_property_4_last_applied_present_when_configured(self, status):
        """
        Feature: launch-config-preapplication, Property 4
        
        For any launchConfigStatus object where status is not
        "not_configured", the lastApplied field must be present and
        contain a valid timestamp.
        """
        if status["status"] != "not_configured":
            # lastApplied must be present (not None)
            assert status["lastApplied"] is not None, (
                f"lastApplied must be present when status is "
                f"'{status['status']}'"
            )
            
            # Verify it's a valid ISO 8601 timestamp
            try:
                parsed = datetime.fromisoformat(
                    status["lastApplied"].replace("Z", "+00:00")
                )
                assert isinstance(parsed, datetime)
            except (ValueError, AttributeError) as e:
                pytest.fail(
                    f"lastApplied '{status['lastApplied']}' is not a valid "
                    f"ISO 8601 timestamp: {e}"
                )

    @given(status=launch_config_status())
    def test_property_4_not_configured_has_null_timestamp(self, status):
        """
        Feature: launch-config-preapplication, Property 4
        
        For any launchConfigStatus object where status is "not_configured",
        the lastApplied field should be None (no configuration has been
        applied yet).
        """
        if status["status"] == "not_configured":
            # lastApplied should be None for not_configured status
            assert status["lastApplied"] is None, (
                "lastApplied should be None when status is 'not_configured'"
            )

    @given(status=launch_config_status())
    def test_property_4_required_fields_present(self, status):
        """
        Feature: launch-config-preapplication, Property 4
        
        For any launchConfigStatus object, all required fields must be
        present: status, lastApplied, appliedBy, serverConfigs, errors.
        """
        required_fields = [
            "status",
            "lastApplied",
            "appliedBy",
            "serverConfigs",
            "errors"
        ]
        
        for field in required_fields:
            assert field in status, (
                f"Required field '{field}' is missing from "
                f"launchConfigStatus"
            )

    @given(status=launch_config_status())
    def test_property_4_server_configs_is_dict(self, status):
        """
        Feature: launch-config-preapplication, Property 4
        
        For any launchConfigStatus object, the serverConfigs field must be
        a dictionary mapping server IDs to server configuration status.
        """
        assert isinstance(status["serverConfigs"], dict), (
            "serverConfigs must be a dictionary"
        )
        
        # Verify each server config has required fields
        for server_id, server_config in status["serverConfigs"].items():
            assert isinstance(server_config, dict), (
                f"Server config for {server_id} must be a dictionary"
            )
            assert "status" in server_config, (
                f"Server config for {server_id} missing 'status' field"
            )
            assert "lastApplied" in server_config, (
                f"Server config for {server_id} missing 'lastApplied' field"
            )
            assert "configHash" in server_config, (
                f"Server config for {server_id} missing 'configHash' field"
            )
            assert "errors" in server_config, (
                f"Server config for {server_id} missing 'errors' field"
            )

    @given(status=launch_config_status())
    def test_property_4_errors_is_list(self, status):
        """
        Feature: launch-config-preapplication, Property 4
        
        For any launchConfigStatus object, the errors field must be a list
        of error message strings.
        """
        assert isinstance(status["errors"], list), (
            "errors must be a list"
        )
        
        # Verify each error is a string
        for error in status["errors"]:
            assert isinstance(error, str), (
                f"Error '{error}' must be a string"
            )

    @given(status=launch_config_status())
    def test_property_4_camel_case_field_names(self, status):
        """
        Feature: launch-config-preapplication, Property 4
        
        For any launchConfigStatus object, all field names must use
        camelCase naming convention (not snake_case).
        """
        # Verify top-level fields use camelCase
        assert "lastApplied" in status  # Not last_applied
        assert "appliedBy" in status  # Not applied_by
        assert "serverConfigs" in status  # Not server_configs
        
        # Verify no snake_case fields
        assert "last_applied" not in status
        assert "applied_by" not in status
        assert "server_configs" not in status
        
        # Verify server config fields use camelCase
        for server_config in status["serverConfigs"].values():
            assert "lastApplied" in server_config  # Not last_applied
            assert "configHash" in server_config  # Not config_hash
            
            # Verify no snake_case fields
            assert "last_applied" not in server_config
            assert "config_hash" not in server_config

    @given(status=launch_config_status())
    def test_property_4_server_status_is_valid(self, status):
        """
        Feature: launch-config-preapplication, Property 4
        
        For any server configuration in serverConfigs, the status field
        must be one of: ready, pending, failed.
        """
        valid_server_statuses = ["ready", "pending", "failed"]
        
        for server_id, server_config in status["serverConfigs"].items():
            assert server_config["status"] in valid_server_statuses, (
                f"Server {server_id} has invalid status "
                f"'{server_config['status']}', must be one of "
                f"{valid_server_statuses}"
            )

    @given(status=launch_config_status())
    def test_property_4_config_hash_format(self, status):
        """
        Feature: launch-config-preapplication, Property 4
        
        For any server configuration with a configHash, it should follow
        the format "sha256:..." or be None.
        """
        for server_id, server_config in status["serverConfigs"].items():
            config_hash = server_config["configHash"]
            
            if config_hash is not None:
                # Verify hash format
                assert isinstance(config_hash, str), (
                    f"Server {server_id} configHash must be a string or None"
                )
                assert config_hash.startswith("sha256:"), (
                    f"Server {server_id} configHash must start with 'sha256:'"
                )
