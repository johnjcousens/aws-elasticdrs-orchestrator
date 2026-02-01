"""
Property-Based Test: Uninitialized Region Handling

Feature: staging-accounts-management
Property 9: For any account query where DRS is not initialized in a region,
that region should contribute zero servers to the account's total count, and
the query should continue successfully for other regions.

**Validates: Requirements 9.4**
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError

# Add lambda directory to path
lambda_dir = Path(__file__).parent.parent.parent / "lambda" / "query-handler"
sys.path.insert(0, str(lambda_dir))

from hypothesis import given, strategies as st, settings, assume
import pytest

# Import the function under test
from index import query_account_capacity, DRS_REGIONS


# ============================================================================
# Hypothesis Strategies
# ============================================================================


@st.composite
def region_initialization_strategy(draw):
    """
    Generate a mapping of regions to initialization status.

    Returns a dict where:
    - Key: region name
    - Value: tuple of (initialized: bool, server_count: int)
    """
    # Select a subset of regions to test (1-15 regions)
    num_regions = draw(st.integers(min_value=1, max_value=len(DRS_REGIONS)))
    selected_regions = draw(
        st.lists(
            st.sampled_from(DRS_REGIONS),
            min_size=num_regions,
            max_size=num_regions,
            unique=True,
        )
    )

    region_status = {}
    for region in selected_regions:
        initialized = draw(st.booleans())
        if initialized:
            # Initialized regions have servers
            server_count = draw(st.integers(min_value=0, max_value=300))
        else:
            # Uninitialized regions have no servers
            server_count = 0

        region_status[region] = (initialized, server_count)

    return region_status


# ============================================================================
# Property Tests
# ============================================================================


@settings(max_examples=100)
@given(region_status=region_initialization_strategy())
def test_property_uninitialized_region_handling(region_status):
    """
    Property 9: Uninitialized Region Handling

    For any account query where DRS is not initialized in some regions:
    1. Uninitialized regions should contribute zero servers
    2. Query should continue successfully for other regions
    3. Total count should only include initialized regions
    4. No errors should be raised for uninitialized regions
    """
    # Create account configuration
    account_config = {
        "accountId": "111111111111",
        "accountName": "Test Account",
        "accountType": "target",
        # No roleArn/externalId means use default credentials
    }

    # Track which regions were queried
    queried_regions = []

    def mock_count_drs_servers(drs_client, account_id):
        """Mock that returns server counts based on region."""
        # Extract region from the client (we'll track this via the mock)
        region = drs_client._client_config.region_name
        queried_regions.append(region)

        if region in region_status:
            initialized, server_count = region_status[region]
            if not initialized:
                # Simulate uninitialized region
                raise ClientError(
                    {
                        "Error": {
                            "Code": "UninitializedAccountException",
                            "Message": f"DRS is not initialized in {region}",
                        }
                    },
                    "DescribeSourceServers",
                )
            else:
                # Return server count for initialized region
                return {
                    "totalServers": server_count,
                    "replicatingServers": server_count,
                }
        else:
            # Region not in our test set - treat as uninitialized
            raise ClientError(
                {
                    "Error": {
                        "Code": "UninitializedAccountException",
                        "Message": f"DRS is not initialized in {region}",
                    }
                },
                "DescribeSourceServers",
            )

    def mock_boto3_client(service, region_name=None, **kwargs):
        """Mock boto3.client to return a mock DRS client."""
        if service == "drs":
            mock_client = MagicMock()
            mock_client._client_config.region_name = region_name
            return mock_client
        else:
            # For other services (like STS), return a real client
            import boto3

            return boto3.client(service, region_name=region_name, **kwargs)

    with patch("index.boto3.client", side_effect=mock_boto3_client):
        with patch(
            "index._count_drs_servers", side_effect=mock_count_drs_servers
        ):
            # Query account capacity
            result = query_account_capacity(account_config)

    # Property 1: Query should succeed (accessible = True)
    assert (
        result["accessible"] is True
    ), "Query should succeed even with uninitialized regions"

    # Property 2: Total servers should only count initialized regions
    expected_total = sum(
        count for initialized, count in region_status.values() if initialized
    )
    assert result["replicatingServers"] == expected_total, (
        f"Expected {expected_total} replicating servers, "
        f"got {result['replicatingServers']}"
    )
    assert (
        result["totalServers"] == expected_total
    ), f"Expected {expected_total} total servers, got {result['totalServers']}"

    # Property 3: Uninitialized regions should not appear in breakdown
    # (or should appear with 0 servers)
    for region_data in result["regionalBreakdown"]:
        region = region_data["region"]
        if region in region_status:
            initialized, expected_count = region_status[region]
            if initialized:
                # Initialized regions should have correct count
                assert (
                    region_data["totalServers"] == expected_count
                ), f"Region {region} should have {expected_count} servers"
            # Uninitialized regions are filtered out in the implementation

    # Property 4: No error field should be present (query succeeded)
    assert (
        "error" not in result
    ), "Query should not have error field when it succeeds"


@settings(max_examples=50)
@given(
    num_initialized=st.integers(min_value=0, max_value=10),
    num_uninitialized=st.integers(min_value=1, max_value=10),
)
def test_property_mixed_region_initialization(
    num_initialized, num_uninitialized
):
    """
    Property: Mixed region initialization

    When some regions are initialized and others are not:
    - Total should only include initialized regions
    - Query should succeed
    - All regions should be attempted
    """
    # Ensure we have enough regions
    assume(num_initialized + num_uninitialized <= len(DRS_REGIONS))

    # Select regions
    all_regions = DRS_REGIONS[: num_initialized + num_uninitialized]
    initialized_regions = set(all_regions[:num_initialized])
    uninitialized_regions = set(all_regions[num_initialized:])

    # Assign server counts to initialized regions
    server_counts = {region: 50 for region in initialized_regions}

    account_config = {
        "accountId": "111111111111",
        "accountName": "Test Account",
        "accountType": "target",
    }

    def mock_count_drs_servers(drs_client, account_id):
        region = drs_client._client_config.region_name

        if region in uninitialized_regions:
            raise ClientError(
                {
                    "Error": {
                        "Code": "UninitializedAccountException",
                        "Message": f"DRS is not initialized in {region}",
                    }
                },
                "DescribeSourceServers",
            )
        elif region in initialized_regions:
            return {
                "totalServers": server_counts[region],
                "replicatingServers": server_counts[region],
            }
        else:
            # Region not in our test set
            return {"totalServers": 0, "replicatingServers": 0}

    def mock_boto3_client(service, region_name=None, **kwargs):
        if service == "drs":
            mock_client = MagicMock()
            mock_client._client_config.region_name = region_name
            return mock_client
        else:
            import boto3

            return boto3.client(service, region_name=region_name, **kwargs)

    with patch("index.boto3.client", side_effect=mock_boto3_client):
        with patch(
            "index._count_drs_servers", side_effect=mock_count_drs_servers
        ):
            result = query_account_capacity(account_config)

    # Verify results
    expected_total = num_initialized * 50
    assert result["replicatingServers"] == expected_total
    assert result["accessible"] is True


@settings(max_examples=50)
@given(num_regions=st.integers(min_value=1, max_value=15))
def test_property_all_regions_uninitialized(num_regions):
    """
    Property: All regions uninitialized

    When all regions are uninitialized:
    - Total servers should be 0
    - Query should still succeed
    - No error should be raised
    """
    assume(num_regions <= len(DRS_REGIONS))

    selected_regions = DRS_REGIONS[:num_regions]

    account_config = {
        "accountId": "111111111111",
        "accountName": "Test Account",
        "accountType": "target",
    }

    def mock_count_drs_servers(drs_client, account_id):
        # All regions are uninitialized
        region = drs_client._client_config.region_name
        raise ClientError(
            {
                "Error": {
                    "Code": "UninitializedAccountException",
                    "Message": f"DRS is not initialized in {region}",
                }
            },
            "DescribeSourceServers",
        )

    def mock_boto3_client(service, region_name=None, **kwargs):
        if service == "drs":
            mock_client = MagicMock()
            mock_client._client_config.region_name = region_name
            return mock_client
        else:
            import boto3

            return boto3.client(service, region_name=region_name, **kwargs)

    with patch("index.boto3.client", side_effect=mock_boto3_client):
        with patch(
            "index._count_drs_servers", side_effect=mock_count_drs_servers
        ):
            result = query_account_capacity(account_config)

    # Verify all regions uninitialized results in zero servers
    assert result["replicatingServers"] == 0
    assert result["totalServers"] == 0
    assert result["accessible"] is True
    assert "error" not in result


# ============================================================================
# Edge Case Tests
# ============================================================================


def test_edge_case_single_region_uninitialized():
    """Edge case: Only one region, and it's uninitialized."""
    account_config = {
        "accountId": "111111111111",
        "accountName": "Test Account",
        "accountType": "target",
    }

    def mock_count_drs_servers(drs_client, account_id):
        raise ClientError(
            {
                "Error": {
                    "Code": "UninitializedAccountException",
                    "Message": "DRS is not initialized",
                }
            },
            "DescribeSourceServers",
        )

    def mock_boto3_client(service, region_name=None, **kwargs):
        if service == "drs":
            mock_client = MagicMock()
            mock_client._client_config.region_name = region_name or "us-east-1"
            return mock_client
        else:
            import boto3

            return boto3.client(service, region_name=region_name, **kwargs)

    with patch("index.boto3.client", side_effect=mock_boto3_client):
        with patch(
            "index._count_drs_servers", side_effect=mock_count_drs_servers
        ):
            result = query_account_capacity(account_config)

    assert result["replicatingServers"] == 0
    assert result["accessible"] is True


def test_edge_case_alternating_initialization():
    """Edge case: Alternating initialized/uninitialized regions."""
    account_config = {
        "accountId": "111111111111",
        "accountName": "Test Account",
        "accountType": "target",
    }

    # Every other region is initialized
    initialized_regions = {
        DRS_REGIONS[i] for i in range(0, len(DRS_REGIONS), 2)
    }

    def mock_count_drs_servers(drs_client, account_id):
        region = drs_client._client_config.region_name

        if region in initialized_regions:
            return {"totalServers": 20, "replicatingServers": 20}
        else:
            raise ClientError(
                {
                    "Error": {
                        "Code": "UninitializedAccountException",
                        "Message": f"DRS is not initialized in {region}",
                    }
                },
                "DescribeSourceServers",
            )

    def mock_boto3_client(service, region_name=None, **kwargs):
        if service == "drs":
            mock_client = MagicMock()
            mock_client._client_config.region_name = region_name
            return mock_client
        else:
            import boto3

            return boto3.client(service, region_name=region_name, **kwargs)

    with patch("index.boto3.client", side_effect=mock_boto3_client):
        with patch(
            "index._count_drs_servers", side_effect=mock_count_drs_servers
        ):
            result = query_account_capacity(account_config)

    # Should have servers from initialized regions only
    expected_total = len(initialized_regions) * 20
    assert result["replicatingServers"] == expected_total
    assert result["accessible"] is True


def test_edge_case_uninitialized_with_error_message_variation():
    """Edge case: Different error message formats for uninitialized regions."""
    account_config = {
        "accountId": "111111111111",
        "accountName": "Test Account",
        "accountType": "target",
    }

    error_messages = [
        "DRS is not initialized",
        "Account not initialized for DRS",
        "Service not initialized in this region",
    ]

    call_count = [0]

    def mock_count_drs_servers(drs_client, account_id):
        # Cycle through different error messages
        msg = error_messages[call_count[0] % len(error_messages)]
        call_count[0] += 1

        raise ClientError(
            {
                "Error": {
                    "Code": "UninitializedAccountException",
                    "Message": msg,
                }
            },
            "DescribeSourceServers",
        )

    def mock_boto3_client(service, region_name=None, **kwargs):
        if service == "drs":
            mock_client = MagicMock()
            mock_client._client_config.region_name = region_name or "us-east-1"
            return mock_client
        else:
            import boto3

            return boto3.client(service, region_name=region_name, **kwargs)

    with patch("index.boto3.client", side_effect=mock_boto3_client):
        with patch(
            "index._count_drs_servers", side_effect=mock_count_drs_servers
        ):
            result = query_account_capacity(account_config)

    # Should handle all error message variations
    assert result["replicatingServers"] == 0
    assert result["accessible"] is True
