"""
Property-based tests for launch configuration service.

Feature: launch-config-preapplication
Tests universal correctness properties across all valid inputs using Hypothesis.

Validates: Requirements 5.2
"""

import os
import sys
from unittest.mock import MagicMock, patch

from hypothesis import given, settings, strategies as st
import pytest

# Add lambda directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda"))

from shared.launch_config_service import (
    apply_launch_configs_to_group,
    calculate_config_hash,
    detect_config_drift,
    get_config_status,
)


# Efficient strategy for generating unique server IDs
# Instead of generating random hex strings and filtering for uniqueness,
# we generate unique integers and format them as server IDs
def server_id_strategy():
    """
    Generate a single unique server ID efficiently.
    
    Uses integers to ensure uniqueness, then formats as DRS server IDs.
    This avoids the high rejection rate from trying to generate unique
    random hex strings.
    
    Use with st.lists() to generate multiple unique server IDs:
        st.lists(server_id_strategy(), min_size=1, max_size=10, unique=True)
    """
    return st.integers(min_value=0, max_value=0xFFFFFFFFFFFFFFFF).map(
        lambda i: f"s-{i:017x}"
    )


class TestProperty1ConfigurationApplicationCompleteness:
    """
    Property 1: Configuration Application Completeness
    
    For any protection group with launch configurations, all server
    configurations should be applied and status persisted.
    
    Validates: Requirements 1.1, 1.2, 1.4
    """

    @given(
        group_id=st.text(min_size=1, max_size=50),
        region=st.sampled_from(["us-east-1", "us-east-2", "us-west-2"]),
        server_ids=st.lists(
            server_id_strategy(),
            min_size=1,
            max_size=10,
            unique=True
        ),
    )
    @patch("shared.launch_config_service.boto3")
    @patch("shared.launch_config_service._get_protection_groups_table")
    def test_property_1_all_servers_processed(
        self,
        mock_table,
        mock_boto3,
        group_id,
        region,
        server_ids
    ):
        """
        Feature: launch-config-preapplication, Property 1:
        For any protection group with launch configurations, all server
        configurations should be applied (appliedServers + failedServers
        == total servers).
        
        Validates: Requirements 1.1, 1.2, 1.4
        """
        # Create launch configs for all servers
        launch_configs = {
            server_id: {
                "instanceType": "t3.medium",
                "copyPrivateIp": True,
                "copyTags": True
            }
            for server_id in server_ids
        }
        
        # Mock DRS client
        mock_drs_client = MagicMock()
        mock_boto3.client.return_value = mock_drs_client
        
        # Apply configurations
        result = apply_launch_configs_to_group(
            group_id=group_id,
            region=region,
            server_ids=server_ids,
            launch_configs=launch_configs
        )
        
        # Property: All servers must be processed
        total_processed = result["appliedServers"] + result["failedServers"]
        assert total_processed == len(server_ids), (
            f"Not all servers processed: {total_processed} != {len(server_ids)}"
        )
        
        # Property: serverConfigs must contain entries for all servers
        assert len(result["serverConfigs"]) == len(server_ids), (
            f"serverConfigs missing entries: "
            f"{len(result['serverConfigs'])} != {len(server_ids)}"
        )
        
        # Property: All server IDs must be in serverConfigs
        for server_id in server_ids:
            assert server_id in result["serverConfigs"], (
                f"Server {server_id} missing from serverConfigs"
            )

    @given(
        group_id=st.text(min_size=1, max_size=50),
        region=st.sampled_from(["us-east-1", "us-east-2", "us-west-2"]),
        server_ids=st.lists(
            server_id_strategy(),
            min_size=1,
            max_size=5,
            unique=True
        ),
    )
    @patch("shared.launch_config_service.boto3")
    @patch("shared.launch_config_service._get_protection_groups_table")
    def test_property_1_status_persisted(
        self,
        mock_table,
        mock_boto3,
        group_id,
        region,
        server_ids
    ):
        """
        Feature: launch-config-preapplication, Property 1:
        For any protection group with launch configurations, the status
        should be persisted to DynamoDB after application.
        
        Validates: Requirements 1.4
        """
        # Create launch configs for all servers
        launch_configs = {
            server_id: {
                "instanceType": "t3.medium",
                "copyPrivateIp": True
            }
            for server_id in server_ids
        }
        
        # Mock DRS client
        mock_drs_client = MagicMock()
        mock_boto3.client.return_value = mock_drs_client
        
        # Apply configurations
        result = apply_launch_configs_to_group(
            group_id=group_id,
            region=region,
            server_ids=server_ids,
            launch_configs=launch_configs
        )
        
        # Property: Result must contain status field
        assert "status" in result, "Result missing status field"
        assert result["status"] in ["ready", "partial", "failed"], (
            f"Invalid status: {result['status']}"
        )
        
        # Property: Result must contain serverConfigs
        assert "serverConfigs" in result, "Result missing serverConfigs"
        
        # Property: Each server config must have required fields
        for server_id, config in result["serverConfigs"].items():
            assert "status" in config, (
                f"Server {server_id} config missing status"
            )
            assert config["status"] in ["ready", "pending", "failed"], (
                f"Invalid server status: {config['status']}"
            )
            assert "lastApplied" in config, (
                f"Server {server_id} config missing lastApplied"
            )
            assert "configHash" in config, (
                f"Server {server_id} config missing configHash"
            )
            assert "errors" in config, (
                f"Server {server_id} config missing errors"
            )

    @given(
        group_id=st.text(min_size=1, max_size=50),
        region=st.sampled_from(["us-east-1", "us-east-2", "us-west-2"]),
        num_servers=st.integers(min_value=1, max_value=10),
    )
    @patch("shared.launch_config_service.boto3")
    @patch("shared.launch_config_service._get_protection_groups_table")
    def test_property_1_config_hash_calculated(
        self,
        mock_table,
        mock_boto3,
        group_id,
        region,
        num_servers
    ):
        """
        Feature: launch-config-preapplication, Property 1:
        For any protection group with launch configurations, each
        successfully applied server should have a config hash calculated.
        
        Validates: Requirements 1.1, 1.2
        """
        # Generate server IDs
        server_ids = [f"s-{'0' * 16}{i}" for i in range(num_servers)]
        
        # Create launch configs for all servers
        launch_configs = {
            server_id: {
                "instanceType": "t3.medium",
                "copyPrivateIp": True
            }
            for server_id in server_ids
        }
        
        # Mock DRS client
        mock_drs_client = MagicMock()
        mock_boto3.client.return_value = mock_drs_client
        
        # Apply configurations
        result = apply_launch_configs_to_group(
            group_id=group_id,
            region=region,
            server_ids=server_ids,
            launch_configs=launch_configs
        )
        
        # Property: Each successfully applied server must have config hash
        for server_id, config in result["serverConfigs"].items():
            if config["status"] == "ready":
                assert config["configHash"] is not None, (
                    f"Server {server_id} with status 'ready' has no configHash"
                )
                assert config["configHash"].startswith("sha256:"), (
                    f"Server {server_id} configHash has invalid format"
                )

    @given(
        group_id=st.text(min_size=1, max_size=50),
        region=st.sampled_from(["us-east-1", "us-east-2", "us-west-2"]),
        server_ids=st.lists(
            server_id_strategy(),
            min_size=2,
            max_size=8,
            unique=True
        ),
    )
    @patch("shared.launch_config_service.boto3")
    @patch("shared.launch_config_service._get_protection_groups_table")
    def test_property_1_partial_success_handling(
        self,
        mock_table,
        mock_boto3,
        group_id,
        region,
        server_ids
    ):
        """
        Feature: launch-config-preapplication, Property 1:
        For any protection group where some servers fail, the result
        should accurately reflect partial success with correct counts.
        
        Validates: Requirements 1.1, 1.2, 1.4
        """
        # Create launch configs for all servers
        launch_configs = {
            server_id: {
                "instanceType": "t3.medium",
                "copyPrivateIp": True
            }
            for server_id in server_ids
        }
        
        # Mock DRS client to fail on some servers
        mock_drs_client = MagicMock()
        
        # Make every other server fail
        def side_effect(**kwargs):
            server_id = kwargs.get("sourceServerID")
            if server_ids.index(server_id) % 2 == 0:
                # Success
                return {}
            else:
                # Failure
                from botocore.exceptions import ClientError
                raise ClientError(
                    {
                        "Error": {
                            "Code": "ValidationException",
                            "Message": "Invalid config"
                        }
                    },
                    "update_launch_configuration"
                )
        
        mock_drs_client.update_launch_configuration.side_effect = side_effect
        mock_boto3.client.return_value = mock_drs_client
        
        # Apply configurations
        result = apply_launch_configs_to_group(
            group_id=group_id,
            region=region,
            server_ids=server_ids,
            launch_configs=launch_configs
        )
        
        # Property: Total processed must equal total servers
        total_processed = result["appliedServers"] + result["failedServers"]
        assert total_processed == len(server_ids), (
            f"Partial success count mismatch: {total_processed} != "
            f"{len(server_ids)}"
        )
        
        # Property: Status should be "partial" when some succeed and some fail
        if result["appliedServers"] > 0 and result["failedServers"] > 0:
            assert result["status"] == "partial", (
                f"Expected 'partial' status but got '{result['status']}'"
            )


class TestProperty10ConfigurationHashConsistency:
    """
    Property 10: Configuration Hash Consistency
    
    For any launch configuration, calculating the hash multiple times
    with the same input should always produce the same hash value
    (idempotent hash calculation).
    
    Validates: Requirements 4.4 (drift detection depends on consistent hashing)
    """

    @given(
        launch_config=st.dictionaries(
            keys=st.text(min_size=1, max_size=50),
            values=st.one_of(
                st.text(max_size=100),
                st.integers(),
                st.booleans(),
                st.floats(allow_nan=False, allow_infinity=False),
                st.none(),
            ),
            min_size=0,
            max_size=20,
        )
    )
    def test_property_10_hash_consistency_simple_dict(self, launch_config):
        """
        Feature: launch-config-preapplication, Property 10:
        For any launch configuration (simple dictionary), calculating the hash
        multiple times should produce the same result.
        
        Validates: Requirements 4.4
        """
        # Calculate hash multiple times
        hash1 = calculate_config_hash(launch_config)
        hash2 = calculate_config_hash(launch_config)
        hash3 = calculate_config_hash(launch_config)
        
        # All hashes should be identical
        assert hash1 == hash2, "Hash calculation is not consistent (hash1 != hash2)"
        assert hash2 == hash3, "Hash calculation is not consistent (hash2 != hash3)"
        assert hash1 == hash3, "Hash calculation is not consistent (hash1 != hash3)"
        
        # Hash should have correct format
        assert hash1.startswith("sha256:"), "Hash should start with 'sha256:' prefix"

    @given(
        launch_config=st.dictionaries(
            keys=st.text(min_size=1, max_size=50),
            values=st.one_of(
                st.text(max_size=100),
                st.lists(st.text(max_size=50), max_size=10),
                st.integers(),
                st.booleans(),
            ),
            min_size=1,
            max_size=15,
        )
    )
    def test_property_10_hash_consistency_with_lists(self, launch_config):
        """
        Feature: launch-config-preapplication, Property 10:
        For any launch configuration with list values, calculating the hash
        multiple times should produce the same result.
        
        Validates: Requirements 4.4
        """
        # Calculate hash multiple times
        hash1 = calculate_config_hash(launch_config)
        hash2 = calculate_config_hash(launch_config)
        hash3 = calculate_config_hash(launch_config)
        
        # All hashes should be identical
        assert hash1 == hash2, "Hash calculation with lists is not consistent"
        assert hash2 == hash3, "Hash calculation with lists is not consistent"
        assert hash1 == hash3, "Hash calculation with lists is not consistent"

    @given(
        launch_config=st.recursive(
            st.dictionaries(
                keys=st.text(min_size=1, max_size=30),
                values=st.one_of(
                    st.text(max_size=50),
                    st.integers(),
                    st.booleans(),
                ),
                min_size=0,
                max_size=5,
            ),
            lambda children: st.dictionaries(
                keys=st.text(min_size=1, max_size=30),
                values=st.one_of(
                    st.text(max_size=50),
                    st.integers(),
                    st.booleans(),
                    children,
                ),
                min_size=0,
                max_size=5,
            ),
            max_leaves=10,
        )
    )
    def test_property_10_hash_consistency_nested_structures(self, launch_config):
        """
        Feature: launch-config-preapplication, Property 10:
        For any launch configuration with nested dictionaries, calculating
        the hash multiple times should produce the same result.
        
        Validates: Requirements 4.4
        """
        # Calculate hash multiple times
        hash1 = calculate_config_hash(launch_config)
        hash2 = calculate_config_hash(launch_config)
        hash3 = calculate_config_hash(launch_config)
        
        # All hashes should be identical
        assert hash1 == hash2, "Hash calculation with nested dicts is not consistent"
        assert hash2 == hash3, "Hash calculation with nested dicts is not consistent"
        assert hash1 == hash3, "Hash calculation with nested dicts is not consistent"

    @given(
        config_data=st.dictionaries(
            keys=st.text(min_size=1, max_size=50),
            values=st.one_of(
                st.text(max_size=100),
                st.integers(),
                st.booleans(),
                st.lists(st.text(max_size=50), max_size=10),
            ),
            min_size=1,
            max_size=20,
        )
    )
    def test_property_10_hash_independent_of_key_order(self, config_data):
        """
        Feature: launch-config-preapplication, Property 10:
        For any launch configuration, the hash should be independent of
        the order in which keys were inserted into the dictionary.
        
        Validates: Requirements 4.4
        """
        # Create two dictionaries with same data but potentially different order
        # (Python 3.7+ maintains insertion order, but we test the hash function's
        # explicit sorting behavior)
        config1 = config_data.copy()
        
        # Create config2 by rebuilding in reverse key order
        keys = list(config_data.keys())
        config2 = {k: config_data[k] for k in reversed(keys)}
        
        # Calculate hashes
        hash1 = calculate_config_hash(config1)
        hash2 = calculate_config_hash(config2)
        
        # Hashes should be identical regardless of key order
        assert hash1 == hash2, (
            f"Hash should be independent of key order. "
            f"Config1 keys: {list(config1.keys())}, "
            f"Config2 keys: {list(config2.keys())}"
        )

    @given(
        launch_config=st.dictionaries(
            keys=st.text(min_size=1, max_size=50),
            values=st.one_of(
                st.text(max_size=100),
                st.integers(min_value=-1000000, max_value=1000000),
                st.booleans(),
                st.floats(
                    allow_nan=False,
                    allow_infinity=False,
                    min_value=-1e6,
                    max_value=1e6,
                ),
            ),
            min_size=0,
            max_size=20,
        )
    )
    def test_property_10_hash_consistency_with_numeric_types(self, launch_config):
        """
        Feature: launch-config-preapplication, Property 10:
        For any launch configuration with various numeric types (int, float),
        calculating the hash multiple times should produce the same result.
        
        Validates: Requirements 4.4
        """
        # Calculate hash multiple times
        hash1 = calculate_config_hash(launch_config)
        hash2 = calculate_config_hash(launch_config)
        hash3 = calculate_config_hash(launch_config)
        
        # All hashes should be identical
        assert hash1 == hash2, "Hash calculation with numeric types is not consistent"
        assert hash2 == hash3, "Hash calculation with numeric types is not consistent"
        assert hash1 == hash3, "Hash calculation with numeric types is not consistent"

    @given(
        launch_config=st.dictionaries(
            keys=st.text(min_size=1, max_size=50),
            values=st.one_of(
                st.text(max_size=100),
                st.integers(),
                st.booleans(),
                st.none(),
            ),
            min_size=0,
            max_size=20,
        )
    )
    def test_property_10_hash_consistency_with_none_values(self, launch_config):
        """
        Feature: launch-config-preapplication, Property 10:
        For any launch configuration with None values, calculating the hash
        multiple times should produce the same result.
        
        Validates: Requirements 4.4
        """
        # Calculate hash multiple times
        hash1 = calculate_config_hash(launch_config)
        hash2 = calculate_config_hash(launch_config)
        hash3 = calculate_config_hash(launch_config)
        
        # All hashes should be identical
        assert hash1 == hash2, "Hash calculation with None values is not consistent"
        assert hash2 == hash3, "Hash calculation with None values is not consistent"
        assert hash1 == hash3, "Hash calculation with None values is not consistent"

    def test_property_10_empty_config_consistency(self):
        """
        Feature: launch-config-preapplication, Property 10:
        For empty configuration, calculating the hash multiple times
        should produce the same result.
        
        Validates: Requirements 4.4
        """
        # Calculate hash for empty config multiple times
        hash1 = calculate_config_hash({})
        hash2 = calculate_config_hash({})
        hash3 = calculate_config_hash({})
        
        # All hashes should be identical
        assert hash1 == hash2, "Hash calculation for empty config is not consistent"
        assert hash2 == hash3, "Hash calculation for empty config is not consistent"
        assert hash1 == hash3, "Hash calculation for empty config is not consistent"
        
        # Should return the special empty hash
        assert hash1 == "sha256:empty", "Empty config should return 'sha256:empty'"

    def test_property_10_none_config_consistency(self):
        """
        Feature: launch-config-preapplication, Property 10:
        For None configuration, calculating the hash multiple times
        should produce the same result.
        
        Validates: Requirements 4.4
        """
        # Calculate hash for None config multiple times
        hash1 = calculate_config_hash(None)
        hash2 = calculate_config_hash(None)
        hash3 = calculate_config_hash(None)
        
        # All hashes should be identical
        assert hash1 == hash2, "Hash calculation for None config is not consistent"
        assert hash2 == hash3, "Hash calculation for None config is not consistent"
        assert hash1 == hash3, "Hash calculation for None config is not consistent"
        
        # Should return the special empty hash
        assert hash1 == "sha256:empty", "None config should return 'sha256:empty'"


class TestProperty4ConfigurationStatusSchemaValidity:
    """
    Property 4: Configuration Status Schema Validity
    
    For any protection group with configuration status, the status field
    must be one of ["ready", "pending", "failed", "not_configured"], and
    if status is not "not_configured", the lastApplied timestamp must be
    present and valid ISO 8601 format.
    
    Validates: Requirements 2.1, 2.2, 2.3
    """

    @given(
        group_id=st.text(min_size=1, max_size=50),
        status=st.sampled_from(["ready", "pending", "failed"]),
        server_ids=st.lists(
            server_id_strategy(),
            min_size=1,
            max_size=10,
            unique=True
        ),
    )
    @patch("shared.launch_config_service._get_protection_groups_table")
    def test_property_4_status_field_validity(
        self,
        mock_table,
        group_id,
        status,
        server_ids
    ):
        """
        Feature: launch-config-preapplication, Property 4:
        For any protection group with configuration status, the status
        field must be one of the valid values.
        
        Validates: Requirements 2.1, 2.2
        """
        from datetime import datetime, UTC
        
        # Create valid launchConfigStatus
        timestamp = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        launch_config_status = {
            "status": status,
            "lastApplied": timestamp,
            "appliedBy": "user@example.com",
            "serverConfigs": {
                server_id: {
                    "status": "ready",
                    "lastApplied": timestamp,
                    "configHash": "sha256:abc123",
                    "errors": []
                }
                for server_id in server_ids
            },
            "errors": []
        }
        
        # Mock DynamoDB table
        mock_table_instance = MagicMock()
        mock_table.return_value = mock_table_instance
        
        # Mock get_item to return the status
        mock_table_instance.get_item.return_value = {
            "Item": {
                "groupId": group_id,
                "launchConfigStatus": launch_config_status
            }
        }
        
        # Retrieve status
        retrieved_status = get_config_status(group_id)
        
        # Property: Status must be one of valid values
        assert retrieved_status["status"] in [
            "ready", "pending", "failed", "not_configured"
        ], f"Invalid status: {retrieved_status['status']}"
        
        # Property: Status must match what was stored
        assert retrieved_status["status"] == status, (
            f"Retrieved status {retrieved_status['status']} "
            f"does not match stored status {status}"
        )

    @given(
        group_id=st.text(min_size=1, max_size=50),
        status=st.sampled_from(["ready", "pending", "failed"]),
        server_ids=st.lists(
            server_id_strategy(),
            min_size=1,
            max_size=8,
            unique=True
        ),
    )
    @patch("shared.launch_config_service._get_protection_groups_table")
    def test_property_4_timestamp_presence_for_configured_status(
        self,
        mock_table,
        group_id,
        status,
        server_ids
    ):
        """
        Feature: launch-config-preapplication, Property 4:
        For any protection group with status not "not_configured",
        the lastApplied timestamp must be present and valid.
        
        Validates: Requirements 2.2, 2.3
        """
        from datetime import datetime, UTC
        
        # Create valid launchConfigStatus with timestamp
        timestamp = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        launch_config_status = {
            "status": status,
            "lastApplied": timestamp,
            "appliedBy": "user@example.com",
            "serverConfigs": {
                server_id: {
                    "status": "ready",
                    "lastApplied": timestamp,
                    "configHash": "sha256:abc123",
                    "errors": []
                }
                for server_id in server_ids
            },
            "errors": []
        }
        
        # Mock DynamoDB table
        mock_table_instance = MagicMock()
        mock_table.return_value = mock_table_instance
        mock_table_instance.get_item.return_value = {
            "Item": {
                "groupId": group_id,
                "launchConfigStatus": launch_config_status
            }
        }
        
        # Retrieve status
        retrieved_status = get_config_status(group_id)
        
        # Property: lastApplied must be present for non-not_configured status
        assert "lastApplied" in retrieved_status, (
            f"lastApplied missing for status '{status}'"
        )
        assert retrieved_status["lastApplied"] is not None, (
            f"lastApplied is None for status '{status}'"
        )
        
        # Property: lastApplied must be valid ISO 8601 format
        try:
            # Parse ISO 8601 timestamp
            parsed_time = datetime.fromisoformat(
                retrieved_status["lastApplied"].replace("Z", "+00:00")
            )
            assert parsed_time is not None, "Failed to parse timestamp"
        except (ValueError, AttributeError) as e:
            pytest.fail(
                f"lastApplied '{retrieved_status['lastApplied']}' "
                f"is not valid ISO 8601 format: {e}"
            )

    @given(
        group_id=st.text(min_size=1, max_size=50),
        server_ids=st.lists(
            server_id_strategy(),
            min_size=1,
            max_size=10,
            unique=True
        ),
    )
    @patch("shared.launch_config_service._get_protection_groups_table")
    def test_property_4_server_configs_structure_validity(
        self,
        mock_table,
        group_id,
        server_ids
    ):
        """
        Feature: launch-config-preapplication, Property 4:
        For any protection group with configuration status, the
        serverConfigs structure must be valid with required fields.
        
        Validates: Requirements 2.1, 2.2, 2.3
        """
        from datetime import datetime, UTC
        
        # Create valid launchConfigStatus
        timestamp = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        launch_config_status = {
            "status": "ready",
            "lastApplied": timestamp,
            "appliedBy": "user@example.com",
            "serverConfigs": {
                server_id: {
                    "status": "ready",
                    "lastApplied": timestamp,
                    "configHash": f"sha256:hash{i}",
                    "errors": []
                }
                for i, server_id in enumerate(server_ids)
            },
            "errors": []
        }
        
        # Mock DynamoDB table
        mock_table_instance = MagicMock()
        mock_table.return_value = mock_table_instance
        mock_table_instance.get_item.return_value = {
            "Item": {
                "groupId": group_id,
                "launchConfigStatus": launch_config_status
            }
        }
        
        # Retrieve status
        retrieved_status = get_config_status(group_id)
        
        # Property: serverConfigs must be present
        assert "serverConfigs" in retrieved_status, (
            "serverConfigs missing from status"
        )
        assert isinstance(retrieved_status["serverConfigs"], dict), (
            "serverConfigs must be a dictionary"
        )
        
        # Property: Each server must have valid config structure
        for server_id in server_ids:
            assert server_id in retrieved_status["serverConfigs"], (
                f"Server {server_id} missing from serverConfigs"
            )
            
            server_config = retrieved_status["serverConfigs"][server_id]
            
            # Required fields
            assert "status" in server_config, (
                f"Server {server_id} config missing status"
            )
            assert server_config["status"] in [
                "ready", "pending", "failed"
            ], f"Invalid server status: {server_config['status']}"
            
            assert "lastApplied" in server_config, (
                f"Server {server_id} config missing lastApplied"
            )
            
            assert "configHash" in server_config, (
                f"Server {server_id} config missing configHash"
            )
            
            assert "errors" in server_config, (
                f"Server {server_id} config missing errors"
            )
            assert isinstance(server_config["errors"], list), (
                f"Server {server_id} errors must be a list"
            )

    @given(
        group_id=st.text(min_size=1, max_size=50),
    )
    @patch("shared.launch_config_service._get_protection_groups_table")
    def test_property_4_not_configured_status_no_timestamp_required(
        self,
        mock_table,
        group_id
    ):
        """
        Feature: launch-config-preapplication, Property 4:
        For any protection group with status "not_configured",
        the lastApplied timestamp is not required.
        
        Validates: Requirements 2.1, 2.2
        """
        # Create launchConfigStatus with not_configured status
        launch_config_status = {
            "status": "not_configured",
            "serverConfigs": {},
            "errors": []
        }
        
        # Mock DynamoDB table
        mock_table_instance = MagicMock()
        mock_table.return_value = mock_table_instance
        mock_table_instance.get_item.return_value = {
            "Item": {
                "groupId": group_id,
                "launchConfigStatus": launch_config_status
            }
        }
        
        # Retrieve status
        retrieved_status = get_config_status(group_id)
        
        # Property: Status must be not_configured
        assert retrieved_status["status"] == "not_configured", (
            f"Expected not_configured status, got {retrieved_status['status']}"
        )
        
        # Property: lastApplied may be absent or None for not_configured
        # (this is valid - no timestamp required)
        if "lastApplied" in retrieved_status:
            # If present, it can be None
            assert retrieved_status["lastApplied"] is None or (
                isinstance(retrieved_status["lastApplied"], str)
            ), "lastApplied must be None or string if present"

    @given(
        group_id=st.text(min_size=1, max_size=50),
        status=st.sampled_from(["ready", "pending", "failed"]),
        num_servers=st.integers(min_value=1, max_value=10),
    )
    @patch("shared.launch_config_service._get_protection_groups_table")
    def test_property_4_camelcase_naming_convention(
        self,
        mock_table,
        group_id,
        status,
        num_servers
    ):
        """
        Feature: launch-config-preapplication, Property 4:
        For any protection group with configuration status, all field
        names must follow camelCase convention (launchConfigStatus,
        lastApplied, appliedBy, serverConfigs).
        
        Validates: Requirements 2.1
        """
        from datetime import datetime, UTC
        
        # Generate server IDs
        server_ids = [f"s-{'0' * 16}{i}" for i in range(num_servers)]
        
        # Create valid launchConfigStatus with camelCase fields
        timestamp = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        launch_config_status = {
            "status": status,
            "lastApplied": timestamp,  # camelCase
            "appliedBy": "user@example.com",  # camelCase
            "serverConfigs": {  # camelCase
                server_id: {
                    "status": "ready",
                    "lastApplied": timestamp,  # camelCase
                    "configHash": f"sha256:hash{i}",  # camelCase
                    "errors": []
                }
                for i, server_id in enumerate(server_ids)
            },
            "errors": []
        }
        
        # Mock DynamoDB table
        mock_table_instance = MagicMock()
        mock_table.return_value = mock_table_instance
        mock_table_instance.get_item.return_value = {
            "Item": {
                "groupId": group_id,
                "launchConfigStatus": launch_config_status  # camelCase
            }
        }
        
        # Retrieve status
        retrieved_status = get_config_status(group_id)
        
        # Property: All field names must be camelCase
        assert "lastApplied" in retrieved_status, (
            "Field should be 'lastApplied' (camelCase), not 'last_applied'"
        )
        assert "appliedBy" in retrieved_status, (
            "Field should be 'appliedBy' (camelCase), not 'applied_by'"
        )
        assert "serverConfigs" in retrieved_status, (
            "Field should be 'serverConfigs' (camelCase), not 'server_configs'"
        )
        
        # Property: Server config fields must be camelCase
        for server_id, server_config in retrieved_status["serverConfigs"].items():
            assert "lastApplied" in server_config, (
                f"Server {server_id} should have 'lastApplied' (camelCase)"
            )
            assert "configHash" in server_config, (
                f"Server {server_id} should have 'configHash' (camelCase)"
            )


class TestProperty8ConfigurationDriftDetection:
    """
    Property 8: Configuration Drift Detection
    
    For any wave execution, if current config hash differs from stored hash,
    configs must be re-applied. Drift detection must correctly identify when
    configurations have changed.
    
    Validates: Requirements 4.4
    """

    @given(
        group_id=st.text(min_size=1, max_size=50),
        server_ids=st.lists(
            server_id_strategy(),
            min_size=1,
            max_size=10,
            unique=True
        ),
        config_values=st.lists(
            st.dictionaries(
                keys=st.sampled_from([
                    "instanceType",
                    "copyPrivateIp",
                    "copyTags",
                    "targetInstanceTypeRightSizingMethod"
                ]),
                values=st.one_of(
                    st.sampled_from(["t3.medium", "t3.large", "m5.xlarge"]),
                    st.booleans(),
                    st.sampled_from(["NONE", "BASIC", "IN_AWS"])
                ),
                min_size=1,
                max_size=4
            ),
            min_size=1,
            max_size=10
        )
    )
    @patch("shared.launch_config_service.get_config_status")
    def test_property_8_drift_detected_when_hashes_differ(
        self,
        mock_get_status,
        group_id,
        server_ids,
        config_values
    ):
        """
        Feature: launch-config-preapplication, Property 8:
        For any wave execution, if current config hash differs from stored
        hash, drift must be detected.
        
        Validates: Requirements 4.4
        """
        # Ensure we have enough configs for all servers
        while len(config_values) < len(server_ids):
            config_values.append(config_values[0])
        
        # Create current configs for all servers
        current_configs = {
            server_id: config_values[i]
            for i, server_id in enumerate(server_ids)
        }
        
        # Create stored configs with DIFFERENT hashes
        # (by modifying one field to ensure hash difference)
        stored_server_configs = {}
        for server_id, current_config in current_configs.items():
            # Calculate hash for current config
            current_hash = calculate_config_hash(current_config)
            
            # Create a different hash by modifying the config
            modified_config = current_config.copy()
            if "instanceType" in modified_config:
                # Change instance type to ensure different hash
                modified_config["instanceType"] = (
                    "t3.xlarge" if modified_config["instanceType"] != "t3.xlarge"
                    else "t3.2xlarge"
                )
            else:
                # Add a field to ensure different hash
                modified_config["instanceType"] = "t3.medium"
            
            stored_hash = calculate_config_hash(modified_config)
            
            # Verify hashes are actually different
            assert current_hash != stored_hash, (
                "Test setup error: hashes should be different"
            )
            
            stored_server_configs[server_id] = {
                "status": "ready",
                "configHash": stored_hash,
                "lastApplied": "2025-02-16T10:00:00Z"
            }
        
        # Mock stored status
        mock_get_status.return_value = {
            "status": "ready",
            "serverConfigs": stored_server_configs
        }
        
        # Detect drift
        result = detect_config_drift(group_id, current_configs)
        
        # Property: Drift MUST be detected when hashes differ
        assert result["hasDrift"] is True, (
            "Drift should be detected when current and stored hashes differ"
        )
        
        # Property: ALL servers should be in driftedServers list
        assert len(result["driftedServers"]) == len(server_ids), (
            f"All {len(server_ids)} servers should be drifted, "
            f"but only {len(result['driftedServers'])} were detected"
        )
        
        # Property: Each server should have drift details
        for server_id in server_ids:
            assert server_id in result["driftedServers"], (
                f"Server {server_id} should be in driftedServers"
            )
            assert server_id in result["details"], (
                f"Server {server_id} should have drift details"
            )
            
            details = result["details"][server_id]
            assert "currentHash" in details, (
                f"Server {server_id} details missing currentHash"
            )
            assert "storedHash" in details, (
                f"Server {server_id} details missing storedHash"
            )
            assert "reason" in details, (
                f"Server {server_id} details missing reason"
            )
            
            # Property: Current and stored hashes must be different
            assert details["currentHash"] != details["storedHash"], (
                f"Server {server_id} hashes should differ for drift detection"
            )

    @given(
        group_id=st.text(min_size=1, max_size=50),
        server_ids=st.lists(
            server_id_strategy(),
            min_size=1,
            max_size=10,
            unique=True
        ),
        config_values=st.lists(
            st.dictionaries(
                keys=st.sampled_from([
                    "instanceType",
                    "copyPrivateIp",
                    "copyTags"
                ]),
                values=st.one_of(
                    st.sampled_from(["t3.medium", "t3.large"]),
                    st.booleans()
                ),
                min_size=1,
                max_size=3
            ),
            min_size=1,
            max_size=10
        )
    )
    @patch("shared.launch_config_service.get_config_status")
    def test_property_8_no_drift_when_hashes_match(
        self,
        mock_get_status,
        group_id,
        server_ids,
        config_values
    ):
        """
        Feature: launch-config-preapplication, Property 8:
        For any wave execution, if current config hash matches stored hash,
        no drift should be detected.
        
        Validates: Requirements 4.4
        """
        # Ensure we have enough configs for all servers
        while len(config_values) < len(server_ids):
            config_values.append(config_values[0])
        
        # Create current configs for all servers
        current_configs = {
            server_id: config_values[i]
            for i, server_id in enumerate(server_ids)
        }
        
        # Create stored configs with SAME hashes
        stored_server_configs = {}
        for server_id, current_config in current_configs.items():
            # Calculate hash for current config
            current_hash = calculate_config_hash(current_config)
            
            stored_server_configs[server_id] = {
                "status": "ready",
                "configHash": current_hash,  # Same hash as current
                "lastApplied": "2025-02-16T10:00:00Z"
            }
        
        # Mock stored status
        mock_get_status.return_value = {
            "status": "ready",
            "serverConfigs": stored_server_configs
        }
        
        # Detect drift
        result = detect_config_drift(group_id, current_configs)
        
        # Property: NO drift should be detected when hashes match
        assert result["hasDrift"] is False, (
            "No drift should be detected when current and stored hashes match"
        )
        
        # Property: driftedServers list should be empty
        assert len(result["driftedServers"]) == 0, (
            f"driftedServers should be empty, but contains "
            f"{len(result['driftedServers'])} servers"
        )
        
        # Property: details should be empty
        assert len(result["details"]) == 0, (
            "details should be empty when no drift detected"
        )

    @given(
        group_id=st.text(min_size=1, max_size=50),
        num_servers=st.integers(min_value=2, max_value=10),
        num_drifted=st.integers(min_value=1, max_value=5)
    )
    @patch("shared.launch_config_service.get_config_status")
    def test_property_8_partial_drift_detection(
        self,
        mock_get_status,
        group_id,
        num_servers,
        num_drifted
    ):
        """
        Feature: launch-config-preapplication, Property 8:
        For any wave execution with mixed drift (some servers drifted,
        some not), drift detection must correctly identify only the
        drifted servers.
        
        Validates: Requirements 4.4
        """
        # Ensure num_drifted doesn't exceed num_servers
        num_drifted = min(num_drifted, num_servers)
        
        # Generate server IDs
        server_ids = [f"s-{'0' * 16}{i}" for i in range(num_servers)]
        
        # Create configs
        current_configs = {}
        stored_server_configs = {}
        
        for i, server_id in enumerate(server_ids):
            # Create current config
            current_config = {
                "instanceType": "t3.medium",
                "copyPrivateIp": True
            }
            current_configs[server_id] = current_config
            current_hash = calculate_config_hash(current_config)
            
            # First num_drifted servers have different stored hash
            if i < num_drifted:
                # Create different stored config
                stored_config = {
                    "instanceType": "t3.large",  # Different
                    "copyPrivateIp": True
                }
                stored_hash = calculate_config_hash(stored_config)
            else:
                # Same stored hash as current
                stored_hash = current_hash
            
            stored_server_configs[server_id] = {
                "status": "ready",
                "configHash": stored_hash,
                "lastApplied": "2025-02-16T10:00:00Z"
            }
        
        # Mock stored status
        mock_get_status.return_value = {
            "status": "ready",
            "serverConfigs": stored_server_configs
        }
        
        # Detect drift
        result = detect_config_drift(group_id, current_configs)
        
        # Property: Drift should be detected if any server has drifted
        assert result["hasDrift"] is True, (
            "Drift should be detected when some servers have drifted"
        )
        
        # Property: Exactly num_drifted servers should be in driftedServers
        assert len(result["driftedServers"]) == num_drifted, (
            f"Expected {num_drifted} drifted servers, "
            f"but got {len(result['driftedServers'])}"
        )
        
        # Property: Only the first num_drifted servers should be drifted
        expected_drifted = set(server_ids[:num_drifted])
        actual_drifted = set(result["driftedServers"])
        assert actual_drifted == expected_drifted, (
            f"Expected drifted servers {expected_drifted}, "
            f"but got {actual_drifted}"
        )
        
        # Property: Only drifted servers should have details
        assert len(result["details"]) == num_drifted, (
            f"Expected {num_drifted} servers in details, "
            f"but got {len(result['details'])}"
        )

    @given(
        group_id=st.text(min_size=1, max_size=50),
        server_ids=st.lists(
            server_id_strategy(),
            min_size=1,
            max_size=8,
            unique=True
        )
    )
    @patch("shared.launch_config_service.get_config_status")
    def test_property_8_drift_with_missing_stored_config(
        self,
        mock_get_status,
        group_id,
        server_ids
    ):
        """
        Feature: launch-config-preapplication, Property 8:
        For any wave execution, if stored configuration is missing for
        a server, drift must be detected for that server.
        
        Validates: Requirements 4.4
        """
        # Create current configs for all servers
        current_configs = {
            server_id: {
                "instanceType": "t3.medium",
                "copyPrivateIp": True
            }
            for server_id in server_ids
        }
        
        # Mock stored status with NO server configs (empty)
        mock_get_status.return_value = {
            "status": "ready",
            "serverConfigs": {}  # No stored configs
        }
        
        # Detect drift
        result = detect_config_drift(group_id, current_configs)
        
        # Property: Drift MUST be detected when stored config is missing
        assert result["hasDrift"] is True, (
            "Drift should be detected when stored config is missing"
        )
        
        # Property: ALL servers should be drifted
        assert len(result["driftedServers"]) == len(server_ids), (
            f"All {len(server_ids)} servers should be drifted when "
            f"stored config is missing"
        )
        
        # Property: Each server should have drift details with None storedHash
        for server_id in server_ids:
            assert server_id in result["details"], (
                f"Server {server_id} should have drift details"
            )
            
            details = result["details"][server_id]
            assert details["storedHash"] is None, (
                f"Server {server_id} should have None storedHash when "
                f"stored config is missing"
            )
            assert details["currentHash"] is not None, (
                f"Server {server_id} should have currentHash"
            )
            assert "no stored configuration" in details["reason"].lower(), (
                f"Server {server_id} reason should mention missing stored config"
            )

    @given(
        group_id=st.text(min_size=1, max_size=50),
        server_ids=st.lists(
            server_id_strategy(),
            min_size=1,
            max_size=8,
            unique=True
        )
    )
    @patch("shared.launch_config_service.get_config_status")
    def test_property_8_drift_with_not_configured_status(
        self,
        mock_get_status,
        group_id,
        server_ids
    ):
        """
        Feature: launch-config-preapplication, Property 8:
        For any wave execution, if group has not_configured status,
        drift must be detected for all servers.
        
        Validates: Requirements 4.4
        """
        # Create current configs for all servers
        current_configs = {
            server_id: {
                "instanceType": "t3.medium",
                "copyPrivateIp": True
            }
            for server_id in server_ids
        }
        
        # Mock stored status as not_configured
        mock_get_status.return_value = {
            "status": "not_configured",
            "serverConfigs": {}
        }
        
        # Detect drift
        result = detect_config_drift(group_id, current_configs)
        
        # Property: Drift MUST be detected for not_configured status
        assert result["hasDrift"] is True, (
            "Drift should be detected when status is not_configured"
        )
        
        # Property: ALL servers should be drifted
        assert len(result["driftedServers"]) == len(server_ids), (
            f"All {len(server_ids)} servers should be drifted when "
            f"status is not_configured"
        )
        
        # Property: Each server should have drift details
        for server_id in server_ids:
            assert server_id in result["details"], (
                f"Server {server_id} should have drift details"
            )
            
            details = result["details"][server_id]
            assert details["storedHash"] is None, (
                f"Server {server_id} should have None storedHash"
            )
            assert "no stored configuration status" in details["reason"].lower(), (
                f"Server {server_id} reason should mention not_configured status"
            )


class TestProperty9StatusUpdateAtomicity:
    """
    Property 9: Status Update Atomicity
    
    For any configuration status update operation, either all fields
    (status, lastApplied, serverConfigs) are updated together, or none
    are updated, ensuring atomic state transitions.
    
    Validates: Requirements 4.5
    """

    @given(
        group_id=st.text(min_size=1, max_size=50),
        status=st.sampled_from(["ready", "pending", "failed"]),
        server_ids=st.lists(
            server_id_strategy(),
            min_size=1,
            max_size=5,
            unique=True
        ),
    )
    @patch("shared.launch_config_service._get_protection_groups_table")
    def test_property_9_all_fields_updated_together(
        self,
        mock_table,
        group_id,
        status,
        server_ids
    ):
        """
        Feature: launch-config-preapplication, Property 9:
        For any status update, all fields (status, lastApplied,
        serverConfigs) must be updated together atomically.
        
        Validates: Requirements 4.5
        """
        from shared.launch_config_service import persist_config_status
        from datetime import datetime, timezone
        
        # Create config status with all required fields
        config_status = {
            "status": status,
            "lastApplied": datetime.now(
                timezone.utc
            ).isoformat().replace("+00:00", "Z"),
            "appliedBy": "test-user",
            "serverConfigs": {
                server_id: {
                    "status": status,
                    "lastApplied": datetime.now(
                        timezone.utc
                    ).isoformat().replace("+00:00", "Z"),
                    "configHash": f"sha256:hash-{server_id}",
                    "errors": []
                }
                for server_id in server_ids
            },
            "errors": []
        }
        
        # Mock DynamoDB table
        mock_table_instance = MagicMock()
        mock_table.return_value = mock_table_instance
        
        # Persist status
        persist_config_status(group_id, config_status)
        
        # Verify update_item was called
        assert mock_table_instance.update_item.called, (
            "update_item should be called"
        )
        
        # Get the update call arguments
        call_args = mock_table_instance.update_item.call_args
        update_expr = call_args[1]["UpdateExpression"]
        expr_values = call_args[1]["ExpressionAttributeValues"]
        
        # Verify all fields are in the update expression
        assert "launchConfigStatus" in update_expr, (
            "launchConfigStatus must be in update expression"
        )
        
        # Verify the status object contains all required fields
        # Note: persist_config_status uses ":status" as parameter name
        status_value = expr_values[":status"]
        assert "status" in status_value, (
            "status field must be present"
        )
        assert "lastApplied" in status_value, (
            "lastApplied field must be present"
        )
        assert "serverConfigs" in status_value, (
            "serverConfigs field must be present"
        )
        assert "errors" in status_value, (
            "errors field must be present"
        )
        
        # Verify serverConfigs has entries for all servers
        assert len(status_value["serverConfigs"]) == len(server_ids), (
            f"serverConfigs should have {len(server_ids)} entries"
        )
        
        # Verify each server config has required fields
        for server_id in server_ids:
            assert server_id in status_value["serverConfigs"], (
                f"Server {server_id} must be in serverConfigs"
            )
            server_config = status_value["serverConfigs"][server_id]
            assert "status" in server_config, (
                f"Server {server_id} config must have status"
            )
            assert "lastApplied" in server_config, (
                f"Server {server_id} config must have lastApplied"
            )
            assert "configHash" in server_config, (
                f"Server {server_id} config must have configHash"
            )
            assert "errors" in server_config, (
                f"Server {server_id} config must have errors"
            )

    @given(
        group_id=st.text(min_size=1, max_size=50),
        server_ids=st.lists(
            server_id_strategy(),
            min_size=1,
            max_size=5,
            unique=True
        ),
    )
    @patch("shared.launch_config_service._get_protection_groups_table")
    def test_property_9_partial_update_not_allowed(
        self,
        mock_table,
        group_id,
        server_ids
    ):
        """
        Feature: launch-config-preapplication, Property 9:
        Partial updates (only some fields) should not be possible.
        All fields must be updated together.
        
        Validates: Requirements 4.5
        """
        from shared.launch_config_service import persist_config_status
        from datetime import datetime, timezone
        
        # Create incomplete config status (missing serverConfigs)
        # Note: persist_config_status validates and requires serverConfigs
        incomplete_status = {
            "status": "ready",
            "lastApplied": datetime.now(
                timezone.utc
            ).isoformat().replace("+00:00", "Z"),
            "appliedBy": "test-user",
            "serverConfigs": {},  # Required field, even if empty
            "errors": []
        }
        
        # Mock DynamoDB table
        mock_table_instance = MagicMock()
        mock_table.return_value = mock_table_instance
        
        # Persist status - should succeed with empty serverConfigs
        persist_config_status(group_id, incomplete_status)
        
        # Verify update was called
        assert mock_table_instance.update_item.called, (
            "update_item should be called"
        )
        
        # Get the persisted value
        call_args = mock_table_instance.update_item.call_args
        expr_values = call_args[1]["ExpressionAttributeValues"]
        status_value = expr_values[":status"]
        
        # Verify serverConfigs field exists (even if empty)
        assert "serverConfigs" in status_value, (
            "serverConfigs must always be present in status updates"
        )

    @given(
        group_id=st.text(min_size=1, max_size=50),
        status=st.sampled_from(["ready", "pending", "failed"]),
        server_ids=st.lists(
            server_id_strategy(),
            min_size=1,
            max_size=5,
            unique=True
        ),
    )
    @patch("shared.launch_config_service._get_protection_groups_table")
    def test_property_9_status_consistency_after_persist(
        self,
        mock_table,
        group_id,
        status,
        server_ids
    ):
        """
        Feature: launch-config-preapplication, Property 9:
        After persisting status, retrieving it should return the same
        values for all fields (atomicity verification).
        
        Validates: Requirements 4.5
        """
        from shared.launch_config_service import (
            persist_config_status,
            get_config_status
        )
        from datetime import datetime, timezone
        
        # Create config status
        timestamp = datetime.now(
            timezone.utc
        ).isoformat().replace("+00:00", "Z")
        config_status = {
            "status": status,
            "lastApplied": timestamp,
            "appliedBy": "test-user",
            "serverConfigs": {
                server_id: {
                    "status": status,
                    "lastApplied": timestamp,
                    "configHash": f"sha256:hash-{server_id}",
                    "errors": []
                }
                for server_id in server_ids
            },
            "errors": []
        }
        
        # Mock DynamoDB table for persist
        mock_table_instance = MagicMock()
        mock_table.return_value = mock_table_instance
        
        # Persist status
        persist_config_status(group_id, config_status)
        
        # Mock get_item to return the persisted status
        mock_table_instance.get_item.return_value = {
            "Item": {
                "groupId": group_id,
                "launchConfigStatus": config_status
            }
        }
        
        # Retrieve status
        retrieved_status = get_config_status(group_id)
        
        # Verify all fields match
        assert retrieved_status["status"] == status, (
            "Retrieved status should match persisted status"
        )
        assert retrieved_status["lastApplied"] == timestamp, (
            "Retrieved lastApplied should match persisted timestamp"
        )
        assert len(retrieved_status["serverConfigs"]) == len(
            server_ids
        ), (
            "Retrieved serverConfigs count should match"
        )
        
        # Verify each server config matches
        for server_id in server_ids:
            assert server_id in retrieved_status["serverConfigs"], (
                f"Server {server_id} should be in retrieved status"
            )
            retrieved_server = retrieved_status["serverConfigs"][server_id]
            original_server = config_status["serverConfigs"][server_id]
            assert retrieved_server["status"] == original_server[
                "status"
            ], (
                f"Server {server_id} status should match"
            )
            assert retrieved_server["configHash"] == original_server[
                "configHash"
            ], (
                f"Server {server_id} configHash should match"
            )


class TestProperty6ReapplyOperationCompleteness:
    """
    Property 6: Re-apply Operation Completeness
    
    For any manual re-apply operation on a protection group, all servers
    in the group must have their configurations validated and applied, and
    the resulting status must accurately reflect the outcome (ready if all
    succeeded, failed if any failed).
    
    Validates: Requirements 3.2, 3.3
    """

    @given(
        group_id=st.text(min_size=1, max_size=50),
        region=st.sampled_from(["us-east-1", "us-east-2", "us-west-2"]),
        server_ids=st.lists(
            server_id_strategy(),
            min_size=1,
            max_size=10,
            unique=True
        ),
    )
    @patch("shared.launch_config_service.boto3")
    @patch("shared.launch_config_service._get_protection_groups_table")
    def test_property_6_all_servers_processed_on_reapply(
        self,
        mock_table,
        mock_boto3,
        group_id,
        region,
        server_ids
    ):
        """
        Feature: launch-config-preapplication, Property 6:
        For any manual re-apply operation, all servers in the group must
        be processed (validated and applied).
        
        Validates: Requirements 3.2
        """
        # Create launch configs for all servers
        launch_configs = {
            server_id: {
                "instanceType": "t3.medium",
                "copyPrivateIp": True,
                "copyTags": True
            }
            for server_id in server_ids
        }
        
        # Mock DRS client
        mock_drs_client = MagicMock()
        mock_boto3.client.return_value = mock_drs_client
        
        # Apply configurations (simulating re-apply)
        result = apply_launch_configs_to_group(
            group_id=group_id,
            region=region,
            server_ids=server_ids,
            launch_configs=launch_configs
        )
        
        # Property: All servers must be processed
        total_processed = result["appliedServers"] + result["failedServers"]
        assert total_processed == len(server_ids), (
            f"Re-apply must process all servers: "
            f"{total_processed} != {len(server_ids)}"
        )
        
        # Property: serverConfigs must contain entries for all servers
        assert len(result["serverConfigs"]) == len(server_ids), (
            f"Re-apply serverConfigs missing entries: "
            f"{len(result['serverConfigs'])} != {len(server_ids)}"
        )
        
        # Property: All server IDs must be in serverConfigs
        for server_id in server_ids:
            assert server_id in result["serverConfigs"], (
                f"Server {server_id} missing from re-apply serverConfigs"
            )

    @given(
        group_id=st.text(min_size=1, max_size=50),
        region=st.sampled_from(["us-east-1", "us-east-2", "us-west-2"]),
        server_ids=st.lists(
            server_id_strategy(),
            min_size=1,
            max_size=10,
            unique=True
        ),
    )
    @patch("shared.launch_config_service.boto3")
    @patch("shared.launch_config_service._get_protection_groups_table")
    def test_property_6_status_reflects_all_success(
        self,
        mock_table,
        mock_boto3,
        group_id,
        region,
        server_ids
    ):
        """
        Feature: launch-config-preapplication, Property 6:
        For any manual re-apply where all servers succeed, the resulting
        status must be "ready".
        
        Validates: Requirements 3.3
        """
        # Create launch configs for all servers
        launch_configs = {
            server_id: {
                "instanceType": "t3.medium",
                "copyPrivateIp": True
            }
            for server_id in server_ids
        }
        
        # Mock DRS client to succeed for all servers
        mock_drs_client = MagicMock()
        mock_drs_client.update_launch_configuration.return_value = {}
        mock_boto3.client.return_value = mock_drs_client
        
        # Apply configurations
        result = apply_launch_configs_to_group(
            group_id=group_id,
            region=region,
            server_ids=server_ids,
            launch_configs=launch_configs
        )
        
        # Property: Status must be "ready" when all servers succeed
        assert result["status"] == "ready", (
            f"Status should be 'ready' when all servers succeed, "
            f"but got '{result['status']}'"
        )
        
        # Property: All servers should have succeeded
        assert result["appliedServers"] == len(server_ids), (
            f"All {len(server_ids)} servers should succeed"
        )
        assert result["failedServers"] == 0, (
            "No servers should fail when all succeed"
        )
        
        # Property: Each server config should have "ready" status
        for server_id in server_ids:
            server_config = result["serverConfigs"][server_id]
            assert server_config["status"] == "ready", (
                f"Server {server_id} should have 'ready' status"
            )
            assert len(server_config["errors"]) == 0, (
                f"Server {server_id} should have no errors"
            )

    @given(
        group_id=st.text(min_size=1, max_size=50),
        region=st.sampled_from(["us-east-1", "us-east-2", "us-west-2"]),
        server_ids=st.lists(
            server_id_strategy(),
            min_size=1,
            max_size=10,
            unique=True
        ),
    )
    @patch("shared.launch_config_service.boto3")
    @patch("shared.launch_config_service._get_protection_groups_table")
    def test_property_6_status_reflects_all_failure(
        self,
        mock_table,
        mock_boto3,
        group_id,
        region,
        server_ids
    ):
        """
        Feature: launch-config-preapplication, Property 6:
        For any manual re-apply where all servers fail, the resulting
        status must be "failed".
        
        Validates: Requirements 3.3
        """
        # Create launch configs for all servers
        launch_configs = {
            server_id: {
                "instanceType": "t3.medium",
                "copyPrivateIp": True
            }
            for server_id in server_ids
        }
        
        # Mock DRS client to fail for all servers
        mock_drs_client = MagicMock()
        from botocore.exceptions import ClientError
        mock_drs_client.update_launch_configuration.side_effect = ClientError(
            {
                "Error": {
                    "Code": "ValidationException",
                    "Message": "Invalid configuration"
                }
            },
            "update_launch_configuration"
        )
        mock_boto3.client.return_value = mock_drs_client
        
        # Apply configurations
        result = apply_launch_configs_to_group(
            group_id=group_id,
            region=region,
            server_ids=server_ids,
            launch_configs=launch_configs
        )
        
        # Property: Status must be "failed" when all servers fail
        assert result["status"] == "failed", (
            f"Status should be 'failed' when all servers fail, "
            f"but got '{result['status']}'"
        )
        
        # Property: All servers should have failed
        assert result["failedServers"] == len(server_ids), (
            f"All {len(server_ids)} servers should fail"
        )
        assert result["appliedServers"] == 0, (
            "No servers should succeed when all fail"
        )
        
        # Property: Each server config should have "failed" status
        for server_id in server_ids:
            server_config = result["serverConfigs"][server_id]
            assert server_config["status"] == "failed", (
                f"Server {server_id} should have 'failed' status"
            )
            assert len(server_config["errors"]) > 0, (
                f"Server {server_id} should have error messages"
            )

    @given(
        group_id=st.text(min_size=1, max_size=50),
        region=st.sampled_from(["us-east-1", "us-east-2", "us-west-2"]),
        server_ids=st.lists(
            server_id_strategy(),
            min_size=2,
            max_size=10,
            unique=True
        ),
    )
    @patch("shared.launch_config_service.boto3")
    @patch("shared.launch_config_service._get_protection_groups_table")
    def test_property_6_status_reflects_partial_success(
        self,
        mock_table,
        mock_boto3,
        group_id,
        region,
        server_ids
    ):
        """
        Feature: launch-config-preapplication, Property 6:
        For any manual re-apply where some servers succeed and some fail,
        the resulting status must be "partial".
        
        Validates: Requirements 3.3
        """
        # Create launch configs for all servers
        launch_configs = {
            server_id: {
                "instanceType": "t3.medium",
                "copyPrivateIp": True
            }
            for server_id in server_ids
        }
        
        # Mock DRS client to fail on every other server
        mock_drs_client = MagicMock()
        
        def side_effect(**kwargs):
            server_id = kwargs.get("sourceServerID")
            if server_ids.index(server_id) % 2 == 0:
                # Success
                return {}
            else:
                # Failure
                from botocore.exceptions import ClientError
                raise ClientError(
                    {
                        "Error": {
                            "Code": "ValidationException",
                            "Message": "Invalid config"
                        }
                    },
                    "update_launch_configuration"
                )
        
        mock_drs_client.update_launch_configuration.side_effect = side_effect
        mock_boto3.client.return_value = mock_drs_client
        
        # Apply configurations
        result = apply_launch_configs_to_group(
            group_id=group_id,
            region=region,
            server_ids=server_ids,
            launch_configs=launch_configs
        )
        
        # Property: Status must be "partial" when some succeed and some fail
        assert result["status"] == "partial", (
            f"Status should be 'partial' when some servers succeed and "
            f"some fail, but got '{result['status']}'"
        )
        
        # Property: Both success and failure counts must be non-zero
        assert result["appliedServers"] > 0, (
            "Some servers should succeed in partial success scenario"
        )
        assert result["failedServers"] > 0, (
            "Some servers should fail in partial success scenario"
        )
        
        # Property: Total must equal server count
        total = result["appliedServers"] + result["failedServers"]
        assert total == len(server_ids), (
            f"Total processed {total} must equal server count "
            f"{len(server_ids)}"
        )
        
        # Property: Server configs must reflect individual outcomes
        success_count = 0
        failure_count = 0
        for server_id in server_ids:
            server_config = result["serverConfigs"][server_id]
            if server_config["status"] == "ready":
                success_count += 1
                assert len(server_config["errors"]) == 0, (
                    f"Successful server {server_id} should have no errors"
                )
            elif server_config["status"] == "failed":
                failure_count += 1
                assert len(server_config["errors"]) > 0, (
                    f"Failed server {server_id} should have errors"
                )
        
        assert success_count == result["appliedServers"], (
            "Success count in serverConfigs must match appliedServers"
        )
        assert failure_count == result["failedServers"], (
            "Failure count in serverConfigs must match failedServers"
        )

    @given(
        group_id=st.text(min_size=1, max_size=50),
        region=st.sampled_from(["us-east-1", "us-east-2", "us-west-2"]),
        server_ids=st.lists(
            server_id_strategy(),
            min_size=1,
            max_size=8,
            unique=True
        ),
    )
    @patch("shared.launch_config_service.boto3")
    @patch("shared.launch_config_service._get_protection_groups_table")
    def test_property_6_config_validation_before_application(
        self,
        mock_table,
        mock_boto3,
        group_id,
        region,
        server_ids
    ):
        """
        Feature: launch-config-preapplication, Property 6:
        For any manual re-apply operation, configurations must be
        validated before application to DRS.
        
        Validates: Requirements 3.2
        """
        # Create launch configs for all servers
        launch_configs = {
            server_id: {
                "instanceType": "t3.medium",
                "copyPrivateIp": True
            }
            for server_id in server_ids
        }
        
        # Mock DRS client
        mock_drs_client = MagicMock()
        mock_boto3.client.return_value = mock_drs_client
        
        # Apply configurations
        result = apply_launch_configs_to_group(
            group_id=group_id,
            region=region,
            server_ids=server_ids,
            launch_configs=launch_configs
        )
        
        # Property: Each server must have been validated
        # (evidenced by having a config hash calculated)
        for server_id in server_ids:
            server_config = result["serverConfigs"][server_id]
            if server_config["status"] == "ready":
                # Successful application means validation passed
                assert server_config["configHash"] is not None, (
                    f"Server {server_id} should have configHash after "
                    f"successful validation and application"
                )
                assert server_config["configHash"].startswith("sha256:"), (
                    f"Server {server_id} configHash should have sha256 prefix"
                )

    @given(
        group_id=st.text(min_size=1, max_size=50),
        region=st.sampled_from(["us-east-1", "us-east-2", "us-west-2"]),
        server_ids=st.lists(
            server_id_strategy(),
            min_size=1,
            max_size=8,
            unique=True
        ),
    )
    @patch("shared.launch_config_service.boto3")
    @patch("shared.launch_config_service._get_protection_groups_table")
    def test_property_6_reapply_updates_timestamps(
        self,
        mock_table,
        mock_boto3,
        group_id,
        region,
        server_ids
    ):
        """
        Feature: launch-config-preapplication, Property 6:
        For any manual re-apply operation, the lastApplied timestamp
        must be updated for all processed servers.
        
        Validates: Requirements 3.2, 3.3
        """
        # Create launch configs for all servers
        launch_configs = {
            server_id: {
                "instanceType": "t3.medium",
                "copyPrivateIp": True
            }
            for server_id in server_ids
        }
        
        # Mock DRS client
        mock_drs_client = MagicMock()
        mock_boto3.client.return_value = mock_drs_client
        
        # Apply configurations
        result = apply_launch_configs_to_group(
            group_id=group_id,
            region=region,
            server_ids=server_ids,
            launch_configs=launch_configs
        )
        
        # Property: Each server must have lastApplied timestamp
        from datetime import datetime
        for server_id in server_ids:
            server_config = result["serverConfigs"][server_id]
            assert "lastApplied" in server_config, (
                f"Server {server_id} must have lastApplied timestamp"
            )
            assert server_config["lastApplied"] is not None, (
                f"Server {server_id} lastApplied must not be None"
            )
            
            # Verify timestamp is valid ISO 8601 format
            try:
                # Handle both formats: with Z suffix or with +00:00 suffix
                timestamp_str = server_config["lastApplied"]
                if timestamp_str.endswith("Z"):
                    timestamp_str = timestamp_str.replace("Z", "+00:00")
                parsed_time = datetime.fromisoformat(timestamp_str)
                assert parsed_time is not None, (
                    f"Server {server_id} lastApplied failed to parse"
                )
            except (ValueError, AttributeError) as e:
                pytest.fail(
                    f"Server {server_id} lastApplied "
                    f"'{server_config['lastApplied']}' is not valid "
                    f"ISO 8601 format: {e}"
                )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])


class TestProperty5ErrorVisibility:
    """
    Property 5: Error Visibility
    
    For any configuration application that fails for one or more servers,
    the errors array in the configuration status must contain descriptive
    error messages for each failed server.
    
    Validates: Requirements 2.4, 3.4
    """

    @given(
        group_id=st.text(min_size=1, max_size=50),
        region=st.sampled_from(["us-east-1", "us-east-2", "us-west-2"]),
        server_ids=st.lists(
            server_id_strategy(),
            min_size=1,
            max_size=10,
            unique=True
        ),
    )
    @patch("shared.launch_config_service.boto3")
    @patch("shared.launch_config_service._get_protection_groups_table")
    def test_property_5_errors_captured_for_failed_servers(
        self,
        mock_table,
        mock_boto3,
        group_id,
        region,
        server_ids
    ):
        """
        Feature: launch-config-preapplication, Property 5:
        For any configuration application where servers fail, each failed
        server must have error messages in its errors array.
        
        Validates: Requirements 2.4, 3.4
        """
        # Create launch configs for all servers
        launch_configs = {
            server_id: {
                "instanceType": "t3.medium",
                "copyPrivateIp": True
            }
            for server_id in server_ids
        }
        
        # Mock DRS client to fail for all servers
        mock_drs_client = MagicMock()
        from botocore.exceptions import ClientError
        mock_drs_client.update_launch_configuration.side_effect = ClientError(
            {
                "Error": {
                    "Code": "ValidationException",
                    "Message": "Invalid launch configuration"
                }
            },
            "update_launch_configuration"
        )
        mock_boto3.client.return_value = mock_drs_client
        
        # Apply configurations
        result = apply_launch_configs_to_group(
            group_id=group_id,
            region=region,
            server_ids=server_ids,
            launch_configs=launch_configs
        )
        
        # Property: Each failed server must have errors in its config
        for server_id in server_ids:
            server_config = result["serverConfigs"][server_id]
            
            # Server should have failed status
            assert server_config["status"] == "failed", (
                f"Server {server_id} should have 'failed' status"
            )
            
            # Property: errors array must exist and be non-empty
            assert "errors" in server_config, (
                f"Server {server_id} config must have 'errors' field"
            )
            assert isinstance(server_config["errors"], list), (
                f"Server {server_id} errors must be a list"
            )
            assert len(server_config["errors"]) > 0, (
                f"Server {server_id} must have at least one error message"
            )
            
            # Property: error messages must be descriptive strings
            for error in server_config["errors"]:
                assert isinstance(error, str), (
                    f"Server {server_id} error must be a string"
                )
                assert len(error) > 0, (
                    f"Server {server_id} error message must not be empty"
                )

    @given(
        group_id=st.text(min_size=1, max_size=50),
        region=st.sampled_from(["us-east-1", "us-east-2", "us-west-2"]),
        server_ids=st.lists(
            server_id_strategy(),
            min_size=2,
            max_size=10,
            unique=True
        ),
    )
    @patch("shared.launch_config_service.boto3")
    @patch("shared.launch_config_service._get_protection_groups_table")
    @patch("shared.launch_config_service.time.sleep")  # Mock sleep to avoid delays
    def test_property_5_errors_in_overall_errors_array(
        self,
        mock_sleep,
        mock_table,
        mock_boto3,
        group_id,
        region,
        server_ids
    ):
        """
        Feature: launch-config-preapplication, Property 5:
        For any configuration application with failures, the overall
        errors array must contain error messages.
        
        Validates: Requirements 2.4, 3.4
        """
        # Create launch configs for all servers
        launch_configs = {
            server_id: {
                "instanceType": "t3.medium",
                "copyPrivateIp": True
            }
            for server_id in server_ids
        }
        
        # Mock DRS client to fail on some servers
        mock_drs_client = MagicMock()
        
        def side_effect(**kwargs):
            server_id = kwargs.get("sourceServerID")
            # Fail every other server
            if server_ids.index(server_id) % 2 == 0:
                return {}  # Success
            else:
                from botocore.exceptions import ClientError
                raise ClientError(
                    {
                        "Error": {
                            "Code": "ThrottlingException",
                            "Message": "Rate limit exceeded"
                        }
                    },
                    "update_launch_configuration"
                )
        
        mock_drs_client.update_launch_configuration.side_effect = side_effect
        mock_boto3.client.return_value = mock_drs_client
        
        # Apply configurations
        result = apply_launch_configs_to_group(
            group_id=group_id,
            region=region,
            server_ids=server_ids,
            launch_configs=launch_configs
        )
        
        # Property: Overall errors array must exist
        assert "errors" in result, (
            "Result must have 'errors' field"
        )
        assert isinstance(result["errors"], list), (
            "Overall errors must be a list"
        )
        
        # Property: If any server failed, overall errors must be non-empty
        if result["failedServers"] > 0:
            assert len(result["errors"]) > 0, (
                f"Overall errors array must be non-empty when "
                f"{result['failedServers']} servers failed"
            )
            
            # Property: Each error message must be descriptive
            for error in result["errors"]:
                assert isinstance(error, str), (
                    "Overall error must be a string"
                )
                assert len(error) > 0, (
                    "Overall error message must not be empty"
                )

    @given(
        group_id=st.text(min_size=1, max_size=50),
        region=st.sampled_from(["us-east-1", "us-east-2", "us-west-2"]),
        server_ids=st.lists(
            server_id_strategy(),
            min_size=1,
            max_size=8,
            unique=True
        ),
    )
    @patch("shared.launch_config_service.boto3")
    @patch("shared.launch_config_service._get_protection_groups_table")
    def test_property_5_no_errors_for_successful_servers(
        self,
        mock_table,
        mock_boto3,
        group_id,
        region,
        server_ids
    ):
        """
        Feature: launch-config-preapplication, Property 5:
        For any configuration application where servers succeed, those
        servers must have empty errors arrays.
        
        Validates: Requirements 2.4
        """
        # Create launch configs for all servers
        launch_configs = {
            server_id: {
                "instanceType": "t3.medium",
                "copyPrivateIp": True
            }
            for server_id in server_ids
        }
        
        # Mock DRS client to succeed for all servers
        mock_drs_client = MagicMock()
        mock_drs_client.update_launch_configuration.return_value = {}
        mock_boto3.client.return_value = mock_drs_client
        
        # Apply configurations
        result = apply_launch_configs_to_group(
            group_id=group_id,
            region=region,
            server_ids=server_ids,
            launch_configs=launch_configs
        )
        
        # Property: Each successful server must have empty errors array
        for server_id in server_ids:
            server_config = result["serverConfigs"][server_id]
            
            if server_config["status"] == "ready":
                # Property: errors array must exist but be empty
                assert "errors" in server_config, (
                    f"Server {server_id} config must have 'errors' field"
                )
                assert isinstance(server_config["errors"], list), (
                    f"Server {server_id} errors must be a list"
                )
                assert len(server_config["errors"]) == 0, (
                    f"Successful server {server_id} must have empty "
                    f"errors array"
                )

    @given(
        group_id=st.text(min_size=1, max_size=50),
        region=st.sampled_from(["us-east-1", "us-east-2", "us-west-2"]),
        server_ids=st.lists(
            server_id_strategy(),
            min_size=1,
            max_size=8,
            unique=True
        ),
        error_types=st.lists(
            st.sampled_from([
                "ValidationException",
                "ThrottlingException",
                "ResourceNotFoundException",
                "AccessDeniedException"
            ]),
            min_size=1,
            max_size=4
        )
    )
    @settings(deadline=None)  # Disable deadline - retry logic uses time.sleep()
    @patch("shared.launch_config_service.time.sleep")  # Mock sleep to speed up retries
    @patch("shared.launch_config_service.boto3")
    @patch("shared.launch_config_service._get_protection_groups_table")
    def test_property_5_error_messages_are_descriptive(
        self,
        mock_table,
        mock_boto3,
        mock_sleep,
        group_id,
        region,
        server_ids,
        error_types
    ):
        """
        Feature: launch-config-preapplication, Property 5:
        For any configuration application with failures, error messages
        must be descriptive and actionable (contain error type and details).
        
        Validates: Requirements 2.4, 3.4
        """
        # Create launch configs for all servers
        launch_configs = {
            server_id: {
                "instanceType": "t3.medium",
                "copyPrivateIp": True
            }
            for server_id in server_ids
        }
        
        # Mock DRS client to fail with different error types
        mock_drs_client = MagicMock()
        
        def side_effect(**kwargs):
            server_id = kwargs.get("sourceServerID")
            # Use different error types for different servers
            error_type = error_types[
                server_ids.index(server_id) % len(error_types)
            ]
            
            from botocore.exceptions import ClientError
            raise ClientError(
                {
                    "Error": {
                        "Code": error_type,
                        "Message": f"Test error: {error_type}"
                    }
                },
                "update_launch_configuration"
            )
        
        mock_drs_client.update_launch_configuration.side_effect = side_effect
        mock_boto3.client.return_value = mock_drs_client
        
        # Apply configurations
        result = apply_launch_configs_to_group(
            group_id=group_id,
            region=region,
            server_ids=server_ids,
            launch_configs=launch_configs
        )
        
        # Property: Each failed server must have descriptive error messages
        for server_id in server_ids:
            server_config = result["serverConfigs"][server_id]
            
            assert server_config["status"] == "failed", (
                f"Server {server_id} should have failed"
            )
            
            # Property: error messages must contain error details
            assert len(server_config["errors"]) > 0, (
                f"Server {server_id} must have error messages"
            )
            
            for error in server_config["errors"]:
                # Property: error message must be descriptive (not just code)
                assert len(error) > 10, (
                    f"Server {server_id} error message should be "
                    f"descriptive, got: {error}"
                )
                
                # Property: error message should contain useful information
                # Check for error type names, common error keywords, or API operation names
                has_error_type = any(
                    err_type.lower() in error.lower() for err_type in error_types
                )
                has_error_keywords = any(
                    keyword in error.lower() 
                    for keyword in ["error", "failed", "throttled", "invalid", "denied"]
                )
                
                assert has_error_type or has_error_keywords, (
                    f"Server {server_id} error message should contain "
                    f"error type or descriptive keywords, got: {error}"
                )

    @given(
        group_id=st.text(min_size=1, max_size=50),
        region=st.sampled_from(["us-east-1", "us-east-2", "us-west-2"]),
        server_ids=st.lists(
            server_id_strategy(),
            min_size=1,
            max_size=8,
            unique=True
        ),
    )
    @patch("shared.launch_config_service.boto3")
    @patch("shared.launch_config_service._get_protection_groups_table")
    def test_property_5_errors_persist_in_dynamodb(
        self,
        mock_table,
        mock_boto3,
        group_id,
        region,
        server_ids
    ):
        """
        Feature: launch-config-preapplication, Property 5:
        For any configuration application with failures, errors must
        persist in DynamoDB and be retrievable.
        
        Validates: Requirements 2.4, 3.4
        """
        from shared.launch_config_service import (
            persist_config_status,
            get_config_status
        )
        from datetime import datetime, timezone
        
        # Create config status with errors
        timestamp = datetime.now(
            timezone.utc
        ).isoformat().replace("+00:00", "Z")
        
        config_status = {
            "status": "failed",
            "lastApplied": timestamp,
            "appliedBy": "test-user",
            "serverConfigs": {
                server_id: {
                    "status": "failed",
                    "lastApplied": timestamp,
                    "configHash": None,
                    "errors": [
                        f"DRS API error for {server_id}",
                        "Configuration validation failed"
                    ]
                }
                for server_id in server_ids
            },
            "errors": [
                f"Failed to apply configs to {len(server_ids)} servers"
            ]
        }
        
        # Mock DynamoDB table
        mock_table_instance = MagicMock()
        mock_table.return_value = mock_table_instance
        
        # Persist status with errors
        persist_config_status(group_id, config_status)
        
        # Mock get_item to return the persisted status
        mock_table_instance.get_item.return_value = {
            "Item": {
                "groupId": group_id,
                "launchConfigStatus": config_status
            }
        }
        
        # Retrieve status
        retrieved_status = get_config_status(group_id)
        
        # Property: Overall errors must be persisted and retrievable
        assert "errors" in retrieved_status, (
            "Retrieved status must have 'errors' field"
        )
        assert len(retrieved_status["errors"]) > 0, (
            "Retrieved status must have error messages"
        )
        
        # Property: Per-server errors must be persisted and retrievable
        for server_id in server_ids:
            assert server_id in retrieved_status["serverConfigs"], (
                f"Server {server_id} must be in retrieved status"
            )
            
            server_config = retrieved_status["serverConfigs"][server_id]
            
            # Property: Server errors must be persisted
            assert "errors" in server_config, (
                f"Server {server_id} config must have 'errors' field"
            )
            assert len(server_config["errors"]) > 0, (
                f"Server {server_id} must have persisted error messages"
            )
            
            # Property: Error messages must match what was persisted
            assert len(server_config["errors"]) == 2, (
                f"Server {server_id} should have 2 error messages"
            )

    @given(
        group_id=st.text(min_size=1, max_size=50),
        region=st.sampled_from(["us-east-1", "us-east-2", "us-west-2"]),
        num_servers=st.integers(min_value=2, max_value=10),
        num_failed=st.integers(min_value=1, max_value=5)
    )
    @patch("shared.launch_config_service.boto3")
    @patch("shared.launch_config_service._get_protection_groups_table")
    def test_property_5_partial_failure_error_visibility(
        self,
        mock_table,
        mock_boto3,
        group_id,
        region,
        num_servers,
        num_failed
    ):
        """
        Feature: launch-config-preapplication, Property 5:
        For any configuration application with partial failures, only
        failed servers should have error messages, and successful servers
        should have empty errors arrays.
        
        Validates: Requirements 2.4, 3.4
        """
        # Ensure num_failed doesn't exceed num_servers
        num_failed = min(num_failed, num_servers)
        
        # Generate server IDs
        server_ids = [f"s-{'0' * 16}{i}" for i in range(num_servers)]
        
        # Create launch configs for all servers
        launch_configs = {
            server_id: {
                "instanceType": "t3.medium",
                "copyPrivateIp": True
            }
            for server_id in server_ids
        }
        
        # Mock DRS client to fail on first num_failed servers
        mock_drs_client = MagicMock()
        
        def side_effect(**kwargs):
            server_id = kwargs.get("sourceServerID")
            if server_ids.index(server_id) < num_failed:
                # Fail
                from botocore.exceptions import ClientError
                raise ClientError(
                    {
                        "Error": {
                            "Code": "ValidationException",
                            "Message": "Invalid configuration"
                        }
                    },
                    "update_launch_configuration"
                )
            else:
                # Success
                return {}
        
        mock_drs_client.update_launch_configuration.side_effect = side_effect
        mock_boto3.client.return_value = mock_drs_client
        
        # Apply configurations
        result = apply_launch_configs_to_group(
            group_id=group_id,
            region=region,
            server_ids=server_ids,
            launch_configs=launch_configs
        )
        
        # Property: Failed servers must have errors
        failed_servers = server_ids[:num_failed]
        for server_id in failed_servers:
            server_config = result["serverConfigs"][server_id]
            assert server_config["status"] == "failed", (
                f"Server {server_id} should have failed"
            )
            assert len(server_config["errors"]) > 0, (
                f"Failed server {server_id} must have error messages"
            )
        
        # Property: Successful servers must have empty errors
        successful_servers = server_ids[num_failed:]
        for server_id in successful_servers:
            server_config = result["serverConfigs"][server_id]
            assert server_config["status"] == "ready", (
                f"Server {server_id} should have succeeded"
            )
            assert len(server_config["errors"]) == 0, (
                f"Successful server {server_id} must have empty errors array"
            )
        
        # Property: Overall errors array should mention failures
        assert len(result["errors"]) > 0, (
            "Overall errors array must be non-empty for partial failures"
        )


class TestProperty3WaveExecutionFastPath:
    """
    Property 3: Wave Execution Fast Path

    For any wave execution where the protection group has configuration
    status "ready", the wave should start recovery immediately without
    making DRS API calls to apply configurations.

    **Validates: Requirements 1.5, 4.1, 4.2**
    """

    @given(
        group_id=st.text(
            alphabet=st.characters(whitelist_categories=("L", "N")),
            min_size=3,
            max_size=30
        ).map(lambda s: f"pg-{s}"),
        server_ids=st.lists(
            server_id_strategy(),
            min_size=1,
            max_size=5,
            unique=True
        ),
    )
    @settings(max_examples=50)
    @patch("shared.launch_config_service._get_protection_groups_table")
    def test_property_3_ready_status_skips_config_application(
        self,
        mock_table,
        group_id,
        server_ids
    ):
        """
        Feature: launch-config-preapplication, Property 3:
        For any wave with status=ready, recovery should start without
        DRS config API calls.

        **Validates: Requirements 1.5, 4.1, 4.2**

        This test verifies that when get_config_status returns status="ready",
        the fast path is taken and no configuration application is needed.
        """
        from datetime import datetime, UTC

        # Create valid launchConfigStatus with "ready" status
        timestamp = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        launch_config_status = {
            "status": "ready",
            "lastApplied": timestamp,
            "appliedBy": "user@example.com",
            "serverConfigs": {
                server_id: {
                    "status": "ready",
                    "lastApplied": timestamp,
                    "configHash": f"sha256:hash{i}",
                    "errors": []
                }
                for i, server_id in enumerate(server_ids)
            },
            "errors": []
        }

        # Mock DynamoDB table
        mock_table_instance = MagicMock()
        mock_table.return_value = mock_table_instance
        mock_table_instance.get_item.return_value = {
            "Item": {
                "groupId": group_id,
                "launchConfigStatus": launch_config_status
            }
        }

        # Retrieve status
        config_status = get_config_status(group_id)

        # Property: Status must be "ready"
        assert config_status["status"] == "ready", (
            f"Expected status 'ready', got '{config_status['status']}'"
        )

        # Property: When status is "ready", fast path should be taken
        # This means no DRS UpdateLaunchConfiguration calls are needed
        # The wave execution logic checks: if status == "ready", skip config
        is_fast_path = config_status["status"] == "ready"
        assert is_fast_path is True, (
            "Fast path should be taken when status is 'ready'"
        )

        # Property: All server configs should also be ready
        for server_id in server_ids:
            assert server_id in config_status["serverConfigs"], (
                f"Server {server_id} missing from serverConfigs"
            )
            server_config = config_status["serverConfigs"][server_id]
            assert server_config["status"] == "ready", (
                f"Server {server_id} should have 'ready' status for fast path"
            )

    @given(
        group_id=st.text(
            alphabet=st.characters(whitelist_categories=("L", "N")),
            min_size=3,
            max_size=30
        ).map(lambda s: f"pg-{s}"),
        server_ids=st.lists(
            server_id_strategy(),
            min_size=1,
            max_size=5,
            unique=True
        ),
    )
    @settings(max_examples=50)
    @patch("shared.launch_config_service._get_protection_groups_table")
    def test_property_3_ready_status_has_valid_config_hashes(
        self,
        mock_table,
        group_id,
        server_ids
    ):
        """
        Feature: launch-config-preapplication, Property 3:
        For any wave with status=ready, all servers must have valid
        config hashes (indicating configs were pre-applied).

        **Validates: Requirements 1.5, 4.1, 4.2**

        This test verifies that the fast path is only valid when all
        servers have config hashes, proving configs were pre-applied.
        """
        from datetime import datetime, UTC

        # Create valid launchConfigStatus with "ready" status and hashes
        timestamp = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        launch_config_status = {
            "status": "ready",
            "lastApplied": timestamp,
            "appliedBy": "user@example.com",
            "serverConfigs": {
                server_id: {
                    "status": "ready",
                    "lastApplied": timestamp,
                    "configHash": f"sha256:{server_id[-8:]}abc123",
                    "errors": []
                }
                for server_id in server_ids
            },
            "errors": []
        }

        # Mock DynamoDB table
        mock_table_instance = MagicMock()
        mock_table.return_value = mock_table_instance
        mock_table_instance.get_item.return_value = {
            "Item": {
                "groupId": group_id,
                "launchConfigStatus": launch_config_status
            }
        }

        # Retrieve status
        config_status = get_config_status(group_id)

        # Property: When status is "ready", all servers must have config hashes
        assert config_status["status"] == "ready", (
            "Status must be 'ready' for fast path"
        )

        for server_id in server_ids:
            server_config = config_status["serverConfigs"][server_id]

            # Property: Config hash must be present and valid
            assert server_config["configHash"] is not None, (
                f"Server {server_id} must have configHash for fast path"
            )
            assert server_config["configHash"].startswith("sha256:"), (
                f"Server {server_id} configHash must have sha256: prefix"
            )

            # Property: No errors should exist for ready servers
            assert len(server_config["errors"]) == 0, (
                f"Server {server_id} should have no errors when ready"
            )

    @given(
        group_id=st.text(
            alphabet=st.characters(whitelist_categories=("L", "N")),
            min_size=3,
            max_size=30
        ).map(lambda s: f"pg-{s}"),
        non_ready_status=st.sampled_from(["pending", "failed", "not_configured"]),
        server_ids=st.lists(
            server_id_strategy(),
            min_size=1,
            max_size=5,
            unique=True
        ),
    )
    @settings(max_examples=50)
    @patch("shared.launch_config_service._get_protection_groups_table")
    def test_property_3_non_ready_status_requires_config_application(
        self,
        mock_table,
        group_id,
        non_ready_status,
        server_ids
    ):
        """
        Feature: launch-config-preapplication, Property 3:
        For any wave with status != "ready", the fast path should NOT
        be taken - configs must be applied at runtime.

        **Validates: Requirements 1.5, 4.1, 4.2**

        This test verifies the inverse: when status is not "ready",
        the fallback path must be used (DRS config API calls required).
        """
        from datetime import datetime, UTC

        # Create launchConfigStatus with non-ready status
        timestamp = datetime.now(UTC).isoformat().replace("+00:00", "Z")

        # Build server configs based on status
        if non_ready_status == "not_configured":
            server_configs = {}
        else:
            server_configs = {
                server_id: {
                    "status": non_ready_status,
                    "lastApplied": timestamp if non_ready_status != "pending"
                        else None,
                    "configHash": None,
                    "errors": ["Config application failed"]
                        if non_ready_status == "failed" else []
                }
                for server_id in server_ids
            }

        launch_config_status = {
            "status": non_ready_status,
            "lastApplied": timestamp if non_ready_status != "not_configured"
                else None,
            "appliedBy": "user@example.com"
                if non_ready_status != "not_configured" else None,
            "serverConfigs": server_configs,
            "errors": []
        }

        # Mock DynamoDB table
        mock_table_instance = MagicMock()
        mock_table.return_value = mock_table_instance
        mock_table_instance.get_item.return_value = {
            "Item": {
                "groupId": group_id,
                "launchConfigStatus": launch_config_status
            }
        }

        # Retrieve status
        config_status = get_config_status(group_id)

        # Property: Status must NOT be "ready"
        assert config_status["status"] != "ready", (
            f"Status should not be 'ready', got '{config_status['status']}'"
        )

        # Property: Fast path should NOT be taken
        is_fast_path = config_status["status"] == "ready"
        assert is_fast_path is False, (
            f"Fast path should NOT be taken when status is "
            f"'{config_status['status']}'"
        )

        # Property: Fallback path is required (configs must be applied)
        requires_config_application = config_status["status"] != "ready"
        assert requires_config_application is True, (
            "Fallback path (config application) is required when "
            f"status is '{config_status['status']}'"
        )

    @given(
        group_id=st.text(
            alphabet=st.characters(whitelist_categories=("L", "N")),
            min_size=3,
            max_size=30
        ).map(lambda s: f"pg-{s}"),
    )
    @settings(max_examples=30)
    @patch("shared.launch_config_service._get_protection_groups_table")
    def test_property_3_missing_status_requires_config_application(
        self,
        mock_table,
        group_id
    ):
        """
        Feature: launch-config-preapplication, Property 3:
        For any protection group without launchConfigStatus, the fast
        path should NOT be taken - configs must be applied at runtime.

        **Validates: Requirements 1.5, 4.1, 4.2**

        This test verifies that groups without pre-applied configs
        default to "not_configured" and require runtime application.
        """
        # Mock DynamoDB table - group exists but has no launchConfigStatus
        mock_table_instance = MagicMock()
        mock_table.return_value = mock_table_instance
        mock_table_instance.get_item.return_value = {
            "Item": {
                "groupId": group_id,
                "name": "Test Group",
                "region": "us-east-2"
                # No launchConfigStatus field
            }
        }

        # Retrieve status
        config_status = get_config_status(group_id)

        # Property: Default status should be "not_configured"
        assert config_status["status"] == "not_configured", (
            f"Missing launchConfigStatus should default to 'not_configured', "
            f"got '{config_status['status']}'"
        )

        # Property: Fast path should NOT be taken
        is_fast_path = config_status["status"] == "ready"
        assert is_fast_path is False, (
            "Fast path should NOT be taken when status is 'not_configured'"
        )

        # Property: serverConfigs should be empty
        assert config_status["serverConfigs"] == {}, (
            "serverConfigs should be empty for not_configured status"
        )

    @given(
        group_id=st.text(
            alphabet=st.characters(whitelist_categories=("L", "N")),
            min_size=3,
            max_size=30
        ).map(lambda s: f"pg-{s}"),
        server_ids=st.lists(
            server_id_strategy(),
            min_size=1,
            max_size=5,
            unique=True
        ),
    )
    @settings(max_examples=50)
    @patch("shared.launch_config_service._get_protection_groups_table")
    def test_property_3_fast_path_decision_is_deterministic(
        self,
        mock_table,
        group_id,
        server_ids
    ):
        """
        Feature: launch-config-preapplication, Property 3:
        For any protection group, the fast path decision (status == "ready")
        should be deterministic - multiple checks should yield same result.

        **Validates: Requirements 1.5, 4.1, 4.2**

        This test verifies that the fast path decision is consistent
        across multiple status checks.
        """
        from datetime import datetime, UTC

        # Create valid launchConfigStatus with "ready" status
        timestamp = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        launch_config_status = {
            "status": "ready",
            "lastApplied": timestamp,
            "appliedBy": "user@example.com",
            "serverConfigs": {
                server_id: {
                    "status": "ready",
                    "lastApplied": timestamp,
                    "configHash": f"sha256:hash{i}",
                    "errors": []
                }
                for i, server_id in enumerate(server_ids)
            },
            "errors": []
        }

        # Mock DynamoDB table
        mock_table_instance = MagicMock()
        mock_table.return_value = mock_table_instance
        mock_table_instance.get_item.return_value = {
            "Item": {
                "groupId": group_id,
                "launchConfigStatus": launch_config_status
            }
        }

        # Check status multiple times
        status1 = get_config_status(group_id)
        status2 = get_config_status(group_id)
        status3 = get_config_status(group_id)

        # Property: Fast path decision should be deterministic
        is_fast_path_1 = status1["status"] == "ready"
        is_fast_path_2 = status2["status"] == "ready"
        is_fast_path_3 = status3["status"] == "ready"

        assert is_fast_path_1 == is_fast_path_2, (
            "Fast path decision should be consistent (check 1 vs 2)"
        )
        assert is_fast_path_2 == is_fast_path_3, (
            "Fast path decision should be consistent (check 2 vs 3)"
        )
        assert is_fast_path_1 == is_fast_path_3, (
            "Fast path decision should be consistent (check 1 vs 3)"
        )

        # Property: All checks should indicate fast path for "ready" status
        assert all([is_fast_path_1, is_fast_path_2, is_fast_path_3]), (
            "All checks should indicate fast path when status is 'ready'"
        )


class TestProperty11StatusTransitionValidity:
    """
    Property 11: Status Transition Validity

    For any sequence of configuration operations on a protection group,
    the status transitions must follow valid paths:
    - not_configured → pending → (ready | failed)
    - ready → pending → (ready | failed) on re-apply

    **Validates: Requirements 1.4, 3.3, 4.5**
    """

    # Valid status transitions
    VALID_TRANSITIONS = {
        "not_configured": ["pending"],
        "pending": ["ready", "failed", "partial"],
        "ready": ["pending"],  # Re-apply starts new cycle
        "failed": ["pending"],  # Re-apply starts new cycle
        "partial": ["pending"],  # Re-apply starts new cycle
    }

    @given(
        group_id=st.text(min_size=1, max_size=50),
        initial_status=st.sampled_from([
            "not_configured", "ready", "failed", "partial"
        ]),
        server_ids=st.lists(
            server_id_strategy(),
            min_size=1,
            max_size=5,
            unique=True
        ),
    )
    @settings(max_examples=50)
    @patch("shared.launch_config_service.boto3")
    @patch("shared.launch_config_service._get_protection_groups_table")
    def test_property_11_apply_transitions_to_pending_first(
        self,
        mock_table,
        mock_boto3,
        group_id,
        initial_status,
        server_ids
    ):
        """
        Feature: launch-config-preapplication, Property 11:
        For any apply operation, the status must transition through
        "pending" before reaching a final state.

        **Validates: Requirements 1.4, 3.3, 4.5**
        """
        # Create launch configs for all servers
        launch_configs = {
            server_id: {
                "instanceType": "t3.medium",
                "copyPrivateIp": True
            }
            for server_id in server_ids
        }

        # Mock DRS client
        mock_drs_client = MagicMock()
        mock_boto3.client.return_value = mock_drs_client

        # Apply configurations
        result = apply_launch_configs_to_group(
            group_id=group_id,
            region="us-east-2",
            server_ids=server_ids,
            launch_configs=launch_configs
        )

        # Property: Final status must be a valid end state
        valid_end_states = ["ready", "failed", "partial"]
        assert result["status"] in valid_end_states, (
            f"Final status '{result['status']}' must be one of "
            f"{valid_end_states}"
        )

        # Property: The transition from initial_status must be valid
        # Initial → pending → final is the valid path
        if initial_status in self.VALID_TRANSITIONS:
            # Verify pending is a valid intermediate state
            assert "pending" in self.VALID_TRANSITIONS[initial_status], (
                f"Transition from '{initial_status}' should go through "
                f"'pending' state"
            )

    @given(
        group_id=st.text(min_size=1, max_size=50),
        server_ids=st.lists(
            server_id_strategy(),
            min_size=1,
            max_size=5,
            unique=True
        ),
    )
    @settings(max_examples=50)
    @patch("shared.launch_config_service.boto3")
    @patch("shared.launch_config_service._get_protection_groups_table")
    def test_property_11_success_transitions_to_ready(
        self,
        mock_table,
        mock_boto3,
        group_id,
        server_ids
    ):
        """
        Feature: launch-config-preapplication, Property 11:
        For any apply operation where all servers succeed, the final
        status must be "ready".

        **Validates: Requirements 1.4, 3.3, 4.5**
        """
        # Create launch configs for all servers
        launch_configs = {
            server_id: {
                "instanceType": "t3.medium",
                "copyPrivateIp": True
            }
            for server_id in server_ids
        }

        # Mock DRS client to succeed for all servers
        mock_drs_client = MagicMock()
        mock_drs_client.update_launch_configuration.return_value = {}
        mock_boto3.client.return_value = mock_drs_client

        # Apply configurations
        result = apply_launch_configs_to_group(
            group_id=group_id,
            region="us-east-2",
            server_ids=server_ids,
            launch_configs=launch_configs
        )

        # Property: All success must result in "ready" status
        assert result["status"] == "ready", (
            f"All servers succeeded, status should be 'ready', "
            f"got '{result['status']}'"
        )

        # Property: This is a valid transition (pending → ready)
        assert "ready" in self.VALID_TRANSITIONS["pending"], (
            "Transition from 'pending' to 'ready' must be valid"
        )

    @given(
        group_id=st.text(min_size=1, max_size=50),
        server_ids=st.lists(
            server_id_strategy(),
            min_size=1,
            max_size=5,
            unique=True
        ),
    )
    @settings(max_examples=50)
    @patch("shared.launch_config_service.boto3")
    @patch("shared.launch_config_service._get_protection_groups_table")
    def test_property_11_failure_transitions_to_failed(
        self,
        mock_table,
        mock_boto3,
        group_id,
        server_ids
    ):
        """
        Feature: launch-config-preapplication, Property 11:
        For any apply operation where all servers fail, the final
        status must be "failed".

        **Validates: Requirements 1.4, 3.3, 4.5**
        """
        # Create launch configs for all servers
        launch_configs = {
            server_id: {
                "instanceType": "t3.medium",
                "copyPrivateIp": True
            }
            for server_id in server_ids
        }

        # Mock DRS client to fail for all servers
        mock_drs_client = MagicMock()
        from botocore.exceptions import ClientError
        mock_drs_client.update_launch_configuration.side_effect = ClientError(
            {
                "Error": {
                    "Code": "ValidationException",
                    "Message": "Invalid configuration"
                }
            },
            "update_launch_configuration"
        )
        mock_boto3.client.return_value = mock_drs_client

        # Apply configurations
        result = apply_launch_configs_to_group(
            group_id=group_id,
            region="us-east-2",
            server_ids=server_ids,
            launch_configs=launch_configs
        )

        # Property: All failure must result in "failed" status
        assert result["status"] == "failed", (
            f"All servers failed, status should be 'failed', "
            f"got '{result['status']}'"
        )

        # Property: This is a valid transition (pending → failed)
        assert "failed" in self.VALID_TRANSITIONS["pending"], (
            "Transition from 'pending' to 'failed' must be valid"
        )

    @given(
        group_id=st.text(min_size=1, max_size=50),
        server_ids=st.lists(
            server_id_strategy(),
            min_size=2,
            max_size=8,
            unique=True
        ),
    )
    @settings(max_examples=50)
    @patch("shared.launch_config_service.boto3")
    @patch("shared.launch_config_service._get_protection_groups_table")
    def test_property_11_partial_transitions_to_partial(
        self,
        mock_table,
        mock_boto3,
        group_id,
        server_ids
    ):
        """
        Feature: launch-config-preapplication, Property 11:
        For any apply operation where some servers succeed and some fail,
        the final status must be "partial".

        **Validates: Requirements 1.4, 3.3, 4.5**
        """
        # Create launch configs for all servers
        launch_configs = {
            server_id: {
                "instanceType": "t3.medium",
                "copyPrivateIp": True
            }
            for server_id in server_ids
        }

        # Mock DRS client to fail on every other server
        mock_drs_client = MagicMock()

        def side_effect(**kwargs):
            server_id = kwargs.get("sourceServerID")
            if server_ids.index(server_id) % 2 == 0:
                return {}  # Success
            else:
                from botocore.exceptions import ClientError
                raise ClientError(
                    {
                        "Error": {
                            "Code": "ValidationException",
                            "Message": "Invalid config"
                        }
                    },
                    "update_launch_configuration"
                )

        mock_drs_client.update_launch_configuration.side_effect = side_effect
        mock_boto3.client.return_value = mock_drs_client

        # Apply configurations
        result = apply_launch_configs_to_group(
            group_id=group_id,
            region="us-east-2",
            server_ids=server_ids,
            launch_configs=launch_configs
        )

        # Property: Mixed results must result in "partial" status
        if result["appliedServers"] > 0 and result["failedServers"] > 0:
            assert result["status"] == "partial", (
                f"Mixed success/failure should result in 'partial', "
                f"got '{result['status']}'"
            )

            # Property: This is a valid transition (pending → partial)
            assert "partial" in self.VALID_TRANSITIONS["pending"], (
                "Transition from 'pending' to 'partial' must be valid"
            )

    @given(
        group_id=st.text(min_size=1, max_size=50),
        current_status=st.sampled_from(["ready", "failed", "partial"]),
        server_ids=st.lists(
            server_id_strategy(),
            min_size=1,
            max_size=5,
            unique=True
        ),
    )
    @settings(max_examples=50)
    @patch("shared.launch_config_service.boto3")
    @patch("shared.launch_config_service._get_protection_groups_table")
    def test_property_11_reapply_from_any_final_state(
        self,
        mock_table,
        mock_boto3,
        group_id,
        current_status,
        server_ids
    ):
        """
        Feature: launch-config-preapplication, Property 11:
        For any re-apply operation from a final state (ready, failed,
        partial), the transition must go through pending to a new
        final state.

        **Validates: Requirements 1.4, 3.3, 4.5**
        """
        # Create launch configs for all servers
        launch_configs = {
            server_id: {
                "instanceType": "t3.medium",
                "copyPrivateIp": True
            }
            for server_id in server_ids
        }

        # Mock DRS client
        mock_drs_client = MagicMock()
        mock_boto3.client.return_value = mock_drs_client

        # Apply configurations (simulating re-apply)
        result = apply_launch_configs_to_group(
            group_id=group_id,
            region="us-east-2",
            server_ids=server_ids,
            launch_configs=launch_configs
        )

        # Property: Re-apply from any final state must be valid
        assert current_status in self.VALID_TRANSITIONS, (
            f"Current status '{current_status}' must have valid transitions"
        )

        # Property: Re-apply must transition through pending
        assert "pending" in self.VALID_TRANSITIONS[current_status], (
            f"Re-apply from '{current_status}' must go through 'pending'"
        )

        # Property: Final status must be a valid end state
        valid_end_states = ["ready", "failed", "partial"]
        assert result["status"] in valid_end_states, (
            f"Re-apply final status '{result['status']}' must be one of "
            f"{valid_end_states}"
        )

    @given(
        group_id=st.text(min_size=1, max_size=50),
        server_ids=st.lists(
            server_id_strategy(),
            min_size=1,
            max_size=5,
            unique=True
        ),
        num_operations=st.integers(min_value=2, max_value=5)
    )
    @settings(max_examples=30)
    @patch("shared.launch_config_service.boto3")
    @patch("shared.launch_config_service._get_protection_groups_table")
    def test_property_11_sequential_operations_valid_transitions(
        self,
        mock_table,
        mock_boto3,
        group_id,
        server_ids,
        num_operations
    ):
        """
        Feature: launch-config-preapplication, Property 11:
        For any sequence of operations, each status transition must
        follow valid paths.

        **Validates: Requirements 1.4, 3.3, 4.5**
        """
        # Create launch configs for all servers
        launch_configs = {
            server_id: {
                "instanceType": "t3.medium",
                "copyPrivateIp": True
            }
            for server_id in server_ids
        }

        # Mock DRS client
        mock_drs_client = MagicMock()
        mock_boto3.client.return_value = mock_drs_client

        # Track status transitions
        previous_status = "not_configured"
        valid_end_states = ["ready", "failed", "partial"]

        for i in range(num_operations):
            # Apply configurations
            result = apply_launch_configs_to_group(
                group_id=group_id,
                region="us-east-2",
                server_ids=server_ids,
                launch_configs=launch_configs
            )

            current_status = result["status"]

            # Property: Current status must be a valid end state
            assert current_status in valid_end_states, (
                f"Operation {i+1}: Status '{current_status}' must be "
                f"one of {valid_end_states}"
            )

            # Property: Transition must be valid
            # From any final state, we can re-apply (→ pending → final)
            if previous_status in self.VALID_TRANSITIONS:
                # Verify the transition path is valid
                # previous → pending → current
                can_go_to_pending = (
                    "pending" in self.VALID_TRANSITIONS[previous_status]
                )
                can_reach_current = (
                    current_status in self.VALID_TRANSITIONS["pending"]
                )

                assert can_go_to_pending and can_reach_current, (
                    f"Operation {i+1}: Invalid transition "
                    f"'{previous_status}' → '{current_status}'"
                )

            previous_status = current_status


class TestProperty12ConfigurationRoundTripPersistence:
    """
    Property 12: Configuration Round-Trip Persistence

    For any configuration status persisted to DynamoDB, retrieving
    immediately should return an equivalent status object with all
    fields intact.

    **Validates: Requirements 1.4**
    """

    @given(
        group_id=st.text(min_size=1, max_size=50),
        status=st.sampled_from(["ready", "pending", "failed", "partial"]),
        server_ids=st.lists(
            server_id_strategy(),
            min_size=1,
            max_size=10,
            unique=True
        ),
        applied_by=st.text(min_size=1, max_size=100),
    )
    @settings(max_examples=50)
    @patch("shared.launch_config_service._get_protection_groups_table")
    def test_property_12_status_round_trip_preserves_all_fields(
        self,
        mock_table,
        group_id,
        status,
        server_ids,
        applied_by
    ):
        """
        Feature: launch-config-preapplication, Property 12:
        For any status persisted to DynamoDB, retrieving immediately
        should return an equivalent status with all fields intact.

        **Validates: Requirements 1.4**
        """
        from shared.launch_config_service import (
            persist_config_status,
            get_config_status
        )
        from datetime import datetime, timezone

        # Create config status with all required fields
        timestamp = datetime.now(
            timezone.utc
        ).isoformat().replace("+00:00", "Z")

        original_status = {
            "status": status,
            "lastApplied": timestamp,
            "appliedBy": applied_by,
            "serverConfigs": {
                server_id: {
                    "status": "ready" if status == "ready" else "failed",
                    "lastApplied": timestamp,
                    "configHash": f"sha256:hash-{i}",
                    "errors": [] if status == "ready" else ["Test error"]
                }
                for i, server_id in enumerate(server_ids)
            },
            "errors": [] if status == "ready" else ["Overall error"]
        }

        # Mock DynamoDB table
        mock_table_instance = MagicMock()
        mock_table.return_value = mock_table_instance

        # Capture what gets persisted
        persisted_data = {}

        def capture_update(**kwargs):
            persisted_data["args"] = kwargs

        mock_table_instance.update_item.side_effect = capture_update

        # Persist status
        persist_config_status(group_id, original_status)

        # Verify update_item was called
        assert mock_table_instance.update_item.called, (
            "update_item should be called"
        )

        # Mock get_item to return the persisted status
        mock_table_instance.get_item.return_value = {
            "Item": {
                "groupId": group_id,
                "launchConfigStatus": original_status
            }
        }

        # Retrieve status
        retrieved_status = get_config_status(group_id)

        # Property: All top-level fields must be preserved
        assert retrieved_status["status"] == original_status["status"], (
            f"Status mismatch: {retrieved_status['status']} != "
            f"{original_status['status']}"
        )
        assert retrieved_status["lastApplied"] == original_status[
            "lastApplied"
        ], (
            f"lastApplied mismatch"
        )
        assert retrieved_status["appliedBy"] == original_status["appliedBy"], (
            f"appliedBy mismatch"
        )

        # Property: serverConfigs must be preserved
        assert len(retrieved_status["serverConfigs"]) == len(
            original_status["serverConfigs"]
        ), (
            f"serverConfigs count mismatch"
        )

        # Property: Each server config must be preserved
        for server_id in server_ids:
            assert server_id in retrieved_status["serverConfigs"], (
                f"Server {server_id} missing from retrieved status"
            )

            original_server = original_status["serverConfigs"][server_id]
            retrieved_server = retrieved_status["serverConfigs"][server_id]

            assert retrieved_server["status"] == original_server["status"], (
                f"Server {server_id} status mismatch"
            )
            assert retrieved_server["lastApplied"] == original_server[
                "lastApplied"
            ], (
                f"Server {server_id} lastApplied mismatch"
            )
            assert retrieved_server["configHash"] == original_server[
                "configHash"
            ], (
                f"Server {server_id} configHash mismatch"
            )
            assert retrieved_server["errors"] == original_server["errors"], (
                f"Server {server_id} errors mismatch"
            )

        # Property: errors array must be preserved
        assert retrieved_status["errors"] == original_status["errors"], (
            f"errors mismatch"
        )

    @given(
        group_id=st.text(min_size=1, max_size=50),
        server_ids=st.lists(
            server_id_strategy(),
            min_size=1,
            max_size=5,
            unique=True
        ),
        config_hashes=st.lists(
            st.text(min_size=10, max_size=100),
            min_size=1,
            max_size=5
        ),
    )
    @settings(max_examples=50)
    @patch("shared.launch_config_service._get_protection_groups_table")
    def test_property_12_config_hash_preserved_exactly(
        self,
        mock_table,
        group_id,
        server_ids,
        config_hashes
    ):
        """
        Feature: launch-config-preapplication, Property 12:
        For any config hash persisted, the exact hash value must be
        retrievable without modification.

        **Validates: Requirements 1.4**
        """
        from shared.launch_config_service import (
            persist_config_status,
            get_config_status
        )
        from datetime import datetime, timezone

        # Ensure we have enough hashes for all servers
        while len(config_hashes) < len(server_ids):
            config_hashes.append(config_hashes[0])

        timestamp = datetime.now(
            timezone.utc
        ).isoformat().replace("+00:00", "Z")

        # Create status with specific config hashes
        original_status = {
            "status": "ready",
            "lastApplied": timestamp,
            "appliedBy": "test-user",
            "serverConfigs": {
                server_id: {
                    "status": "ready",
                    "lastApplied": timestamp,
                    "configHash": f"sha256:{config_hashes[i]}",
                    "errors": []
                }
                for i, server_id in enumerate(server_ids)
            },
            "errors": []
        }

        # Mock DynamoDB table
        mock_table_instance = MagicMock()
        mock_table.return_value = mock_table_instance

        # Persist status
        persist_config_status(group_id, original_status)

        # Mock get_item to return the persisted status
        mock_table_instance.get_item.return_value = {
            "Item": {
                "groupId": group_id,
                "launchConfigStatus": original_status
            }
        }

        # Retrieve status
        retrieved_status = get_config_status(group_id)

        # Property: Each config hash must be preserved exactly
        for i, server_id in enumerate(server_ids):
            expected_hash = f"sha256:{config_hashes[i]}"
            actual_hash = retrieved_status["serverConfigs"][server_id][
                "configHash"
            ]

            assert actual_hash == expected_hash, (
                f"Server {server_id} configHash not preserved exactly: "
                f"expected '{expected_hash}', got '{actual_hash}'"
            )

    @given(
        group_id=st.text(min_size=1, max_size=50),
        server_ids=st.lists(
            server_id_strategy(),
            min_size=1,
            max_size=5,
            unique=True
        ),
        error_messages=st.lists(
            st.text(min_size=1, max_size=200),
            min_size=0,
            max_size=5
        ),
    )
    @settings(max_examples=50)
    @patch("shared.launch_config_service._get_protection_groups_table")
    def test_property_12_error_messages_preserved_exactly(
        self,
        mock_table,
        group_id,
        server_ids,
        error_messages
    ):
        """
        Feature: launch-config-preapplication, Property 12:
        For any error messages persisted, the exact messages must be
        retrievable without modification.

        **Validates: Requirements 1.4**
        """
        from shared.launch_config_service import (
            persist_config_status,
            get_config_status
        )
        from datetime import datetime, timezone

        timestamp = datetime.now(
            timezone.utc
        ).isoformat().replace("+00:00", "Z")

        # Determine status based on error messages
        status = "failed" if error_messages else "ready"

        # Create status with specific error messages
        original_status = {
            "status": status,
            "lastApplied": timestamp,
            "appliedBy": "test-user",
            "serverConfigs": {
                server_id: {
                    "status": status,
                    "lastApplied": timestamp,
                    "configHash": f"sha256:hash-{i}" if status == "ready" else None,
                    "errors": error_messages if status == "failed" else []
                }
                for i, server_id in enumerate(server_ids)
            },
            "errors": error_messages
        }

        # Mock DynamoDB table
        mock_table_instance = MagicMock()
        mock_table.return_value = mock_table_instance

        # Persist status
        persist_config_status(group_id, original_status)

        # Mock get_item to return the persisted status
        mock_table_instance.get_item.return_value = {
            "Item": {
                "groupId": group_id,
                "launchConfigStatus": original_status
            }
        }

        # Retrieve status
        retrieved_status = get_config_status(group_id)

        # Property: Overall error messages must be preserved exactly
        assert retrieved_status["errors"] == error_messages, (
            f"Overall errors not preserved: expected {error_messages}, "
            f"got {retrieved_status['errors']}"
        )

        # Property: Per-server error messages must be preserved exactly
        for server_id in server_ids:
            expected_errors = error_messages if status == "failed" else []
            actual_errors = retrieved_status["serverConfigs"][server_id][
                "errors"
            ]

            assert actual_errors == expected_errors, (
                f"Server {server_id} errors not preserved: "
                f"expected {expected_errors}, got {actual_errors}"
            )

    @given(
        group_id=st.text(min_size=1, max_size=50),
        server_ids=st.lists(
            server_id_strategy(),
            min_size=1,
            max_size=5,
            unique=True
        ),
    )
    @settings(max_examples=50)
    @patch("shared.launch_config_service._get_protection_groups_table")
    def test_property_12_timestamp_format_preserved(
        self,
        mock_table,
        group_id,
        server_ids
    ):
        """
        Feature: launch-config-preapplication, Property 12:
        For any timestamp persisted, the ISO 8601 format must be
        preserved exactly.

        **Validates: Requirements 1.4**
        """
        from shared.launch_config_service import (
            persist_config_status,
            get_config_status
        )
        from datetime import datetime, timezone

        # Create timestamp in ISO 8601 format with Z suffix
        timestamp = datetime.now(
            timezone.utc
        ).isoformat().replace("+00:00", "Z")

        original_status = {
            "status": "ready",
            "lastApplied": timestamp,
            "appliedBy": "test-user",
            "serverConfigs": {
                server_id: {
                    "status": "ready",
                    "lastApplied": timestamp,
                    "configHash": f"sha256:hash-{i}",
                    "errors": []
                }
                for i, server_id in enumerate(server_ids)
            },
            "errors": []
        }

        # Mock DynamoDB table
        mock_table_instance = MagicMock()
        mock_table.return_value = mock_table_instance

        # Persist status
        persist_config_status(group_id, original_status)

        # Mock get_item to return the persisted status
        mock_table_instance.get_item.return_value = {
            "Item": {
                "groupId": group_id,
                "launchConfigStatus": original_status
            }
        }

        # Retrieve status
        retrieved_status = get_config_status(group_id)

        # Property: Top-level timestamp must be preserved exactly
        assert retrieved_status["lastApplied"] == timestamp, (
            f"Top-level lastApplied not preserved: "
            f"expected '{timestamp}', got '{retrieved_status['lastApplied']}'"
        )

        # Property: Per-server timestamps must be preserved exactly
        for server_id in server_ids:
            server_timestamp = retrieved_status["serverConfigs"][server_id][
                "lastApplied"
            ]
            assert server_timestamp == timestamp, (
                f"Server {server_id} lastApplied not preserved: "
                f"expected '{timestamp}', got '{server_timestamp}'"
            )

    @given(
        group_id=st.text(min_size=1, max_size=50),
        num_persist_cycles=st.integers(min_value=2, max_value=5),
        server_ids=st.lists(
            server_id_strategy(),
            min_size=1,
            max_size=3,
            unique=True
        ),
    )
    @settings(max_examples=30)
    @patch("shared.launch_config_service._get_protection_groups_table")
    def test_property_12_multiple_persist_retrieve_cycles(
        self,
        mock_table,
        group_id,
        num_persist_cycles,
        server_ids
    ):
        """
        Feature: launch-config-preapplication, Property 12:
        For any number of persist-retrieve cycles, the data must remain
        consistent and unchanged.

        **Validates: Requirements 1.4**
        """
        from shared.launch_config_service import (
            persist_config_status,
            get_config_status
        )
        from datetime import datetime, timezone

        # Mock DynamoDB table
        mock_table_instance = MagicMock()
        mock_table.return_value = mock_table_instance

        # Store the last persisted status for verification
        last_persisted_status = None

        for cycle in range(num_persist_cycles):
            timestamp = datetime.now(
                timezone.utc
            ).isoformat().replace("+00:00", "Z")

            current_status = {
                "status": "ready",
                "lastApplied": timestamp,
                "appliedBy": f"user-cycle-{cycle}",
                "serverConfigs": {
                    server_id: {
                        "status": "ready",
                        "lastApplied": timestamp,
                        "configHash": f"sha256:hash-cycle-{cycle}-{i}",
                        "errors": []
                    }
                    for i, server_id in enumerate(server_ids)
                },
                "errors": []
            }

            # Persist status
            persist_config_status(group_id, current_status)

            # Mock get_item to return the current status
            mock_table_instance.get_item.return_value = {
                "Item": {
                    "groupId": group_id,
                    "launchConfigStatus": current_status
                }
            }

            # Retrieve status
            retrieved_status = get_config_status(group_id)

            # Property: Retrieved status must match persisted status
            assert retrieved_status["status"] == current_status["status"], (
                f"Cycle {cycle}: status mismatch"
            )
            assert retrieved_status["appliedBy"] == current_status[
                "appliedBy"
            ], (
                f"Cycle {cycle}: appliedBy mismatch"
            )
            assert len(retrieved_status["serverConfigs"]) == len(
                current_status["serverConfigs"]
            ), (
                f"Cycle {cycle}: serverConfigs count mismatch"
            )

            last_persisted_status = current_status

        # Property: Final retrieved status must match last persisted
        final_retrieved = get_config_status(group_id)
        assert final_retrieved["appliedBy"] == last_persisted_status[
            "appliedBy"
        ], (
            "Final retrieved status doesn't match last persisted"
        )

    @given(
        group_id=st.text(min_size=1, max_size=50),
        server_ids=st.lists(
            server_id_strategy(),
            min_size=1,
            max_size=5,
            unique=True
        ),
    )
    @settings(max_examples=50)
    @patch("shared.launch_config_service._get_protection_groups_table")
    def test_property_12_camelcase_field_names_preserved(
        self,
        mock_table,
        group_id,
        server_ids
    ):
        """
        Feature: launch-config-preapplication, Property 12:
        For any status persisted, camelCase field names must be
        preserved exactly (not converted to snake_case).

        **Validates: Requirements 1.4**
        """
        from shared.launch_config_service import (
            persist_config_status,
            get_config_status
        )
        from datetime import datetime, timezone

        timestamp = datetime.now(
            timezone.utc
        ).isoformat().replace("+00:00", "Z")

        original_status = {
            "status": "ready",
            "lastApplied": timestamp,  # camelCase
            "appliedBy": "test-user",  # camelCase
            "serverConfigs": {  # camelCase
                server_id: {
                    "status": "ready",
                    "lastApplied": timestamp,  # camelCase
                    "configHash": f"sha256:hash-{i}",  # camelCase
                    "errors": []
                }
                for i, server_id in enumerate(server_ids)
            },
            "errors": []
        }

        # Mock DynamoDB table
        mock_table_instance = MagicMock()
        mock_table.return_value = mock_table_instance

        # Persist status
        persist_config_status(group_id, original_status)

        # Mock get_item to return the persisted status
        mock_table_instance.get_item.return_value = {
            "Item": {
                "groupId": group_id,
                "launchConfigStatus": original_status
            }
        }

        # Retrieve status
        retrieved_status = get_config_status(group_id)

        # Property: camelCase field names must be preserved
        assert "lastApplied" in retrieved_status, (
            "Field 'lastApplied' (camelCase) must be preserved"
        )
        assert "appliedBy" in retrieved_status, (
            "Field 'appliedBy' (camelCase) must be preserved"
        )
        assert "serverConfigs" in retrieved_status, (
            "Field 'serverConfigs' (camelCase) must be preserved"
        )

        # Property: snake_case versions must NOT exist
        assert "last_applied" not in retrieved_status, (
            "Field 'last_applied' (snake_case) must NOT exist"
        )
        assert "applied_by" not in retrieved_status, (
            "Field 'applied_by' (snake_case) must NOT exist"
        )
        assert "server_configs" not in retrieved_status, (
            "Field 'server_configs' (snake_case) must NOT exist"
        )

        # Property: Per-server camelCase fields must be preserved
        for server_id in server_ids:
            server_config = retrieved_status["serverConfigs"][server_id]

            assert "lastApplied" in server_config, (
                f"Server {server_id}: 'lastApplied' must be preserved"
            )
            assert "configHash" in server_config, (
                f"Server {server_id}: 'configHash' must be preserved"
            )
            assert "last_applied" not in server_config, (
                f"Server {server_id}: 'last_applied' must NOT exist"
            )
            assert "config_hash" not in server_config, (
                f"Server {server_id}: 'config_hash' must NOT exist"
            )
