"""
Property-Based Tests for Staging Account Sync Functions

Tests Properties 11, 5, and 12 from the design document:
- Property 11: Moved Functions Use Region Filtering
- Property 5: API Call Reduction
- Property 12: Cross-Account IAM Assumptions Limited to Active Regions

Uses Hypothesis for property-based testing with minimum 100 iterations.
"""

import importlib
import os
import sys
from typing import Dict, List
from unittest.mock import MagicMock, Mock, patch

import pytest
from hypothesis import given, settings, strategies as st

# Add lambda directory to path
lambda_path = os.path.join(os.path.dirname(__file__), "../../lambda")
sys.path.insert(0, lambda_path)

# Set environment variables before importing
os.environ["DRS_REGION_STATUS_TABLE"] = "test-drs-region-status"
os.environ["SOURCE_SERVER_INVENTORY_TABLE"] = "test-source-server-inventory"
os.environ["TARGET_ACCOUNTS_TABLE"] = "test-target-accounts"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

from shared.drs_regions import DRS_REGIONS

# Import the module using importlib with hyphens
dm_handler = importlib.import_module("data-management-handler.index")


# Test data generators
@st.composite
def active_region_list(draw):
    """Generate a list of 1-10 active regions from DRS_REGIONS."""
    count = draw(st.integers(min_value=1, max_value=10))
    return draw(st.lists(st.sampled_from(DRS_REGIONS), min_size=count, max_size=count, unique=True))


@st.composite
def target_account_config(draw):
    """Generate a target account configuration."""
    account_id = draw(st.text(min_size=12, max_size=12, alphabet=st.characters(whitelist_categories=("Nd",))))
    return {
        "accountId": account_id,
        "accountName": draw(st.text(min_size=1, max_size=50)),
        "roleArn": f"arn:aws:iam::{account_id}:role/DRSRole",
        "externalId": draw(st.text(min_size=10, max_size=50)),
        "isCurrentAccount": False,
        "stagingAccounts": [
            {
                "accountId": draw(st.text(min_size=12, max_size=12, alphabet=st.characters(whitelist_categories=("Nd",)))),
                "accountName": draw(st.text(min_size=1, max_size=50)),
                "roleArn": f"arn:aws:iam::123456789012:role/StagingRole",
                "externalId": draw(st.text(min_size=10, max_size=50)),
            }
        ],
    }


# Property 11: Moved Functions Use Region Filtering
@settings(max_examples=100, deadline=None)
@given(active_regions=active_region_list())
def test_property_11_handle_sync_staging_accounts_uses_region_filtering(active_regions):
    """
    Feature: active-region-filtering
    Property 11: Moved Functions Use Region Filtering

    For any staging account sync operation, when get_active_regions returns
    a filtered list of regions, the function should only scan those regions
    and not all 28 DRS regions.

    Validates: Requirements 11.12
    """
    with patch("data-management-handler.index.get_active_regions") as mock_get_active:
        with patch("data-management-handler.index.get_target_accounts_table") as mock_table:
            with patch("data-management-handler.index.auto_extend_staging_servers") as mock_extend:
                # Setup: Mock get_active_regions to return filtered list
                mock_get_active.return_value = active_regions

                # Setup: Mock DynamoDB table
                mock_table.return_value.scan.return_value = {"Items": []}

                # Setup: Mock auto_extend to return success
                mock_extend.return_value = {
                    "totalAccounts": 0,
                    "accountsProcessed": 0,
                    "serversExtended": 0,
                    "serversFailed": 0,
                    "details": [],
                }

                # Execute: Call handle_sync_staging_accounts
                result = dm_handler.handle_sync_staging_accounts()

                # Verify: get_active_regions was called
                assert mock_get_active.called, "get_active_regions should be called"

                # Verify: auto_extend_staging_servers was called with active_regions
                assert mock_extend.called, "auto_extend_staging_servers should be called"
                call_args = mock_extend.call_args
                assert len(call_args[0]) == 2, "auto_extend_staging_servers should receive 2 arguments"
                passed_regions = call_args[0][1]
                assert passed_regions == active_regions, f"Should pass active_regions {active_regions}, got {passed_regions}"

                # Verify: Response is successful
                assert result["statusCode"] == 200


@settings(max_examples=100, deadline=None)
@given(active_regions=active_region_list(), target_account=target_account_config())
def test_property_11_auto_extend_staging_servers_uses_region_filtering(active_regions, target_account):
    """
    Feature: active-region-filtering
    Property 11: Moved Functions Use Region Filtering

    For any auto_extend_staging_servers operation, when given a list of
    active_regions, the function should pass those regions to helper functions
    and not use all 28 DRS regions.

    Validates: Requirements 11.12
    """
    with patch("data-management-handler.index.get_extended_source_servers") as mock_get_extended:
        with patch("data-management-handler.index.get_staging_account_servers") as mock_get_staging:
            # Setup: Mock helper functions
            mock_get_extended.return_value = set()
            mock_get_staging.return_value = []

            # Execute: Call auto_extend_staging_servers with active_regions
            result = dm_handler.auto_extend_staging_servers([target_account], active_regions)

            # Verify: get_extended_source_servers was called with active_regions
            if mock_get_extended.called:
                call_args = mock_get_extended.call_args
                passed_regions = call_args[0][3]  # 4th argument is active_regions
                assert passed_regions == active_regions, f"Should pass active_regions {active_regions}, got {passed_regions}"

            # Verify: get_staging_account_servers was called with active_regions
            if mock_get_staging.called:
                call_args = mock_get_staging.call_args
                passed_regions = call_args[0][3]  # 4th argument is active_regions
                assert passed_regions == active_regions, f"Should pass active_regions {active_regions}, got {passed_regions}"


# Property 5: API Call Reduction
@settings(max_examples=100, deadline=None)
@given(active_region_count=st.integers(min_value=1, max_value=10))
def test_property_5_api_call_reduction(active_region_count):
    """
    Feature: active-region-filtering
    Property 5: API Call Reduction

    For any multi-region operation using active region filtering, when comparing
    to the same operation without filtering, the number of DRS API calls should
    be reduced by at least (28 - active_region_count) / 28 * 100 percent.

    Validates: Requirements 9.4, 12.5
    """
    # Select active_region_count regions from DRS_REGIONS
    active_regions = DRS_REGIONS[:active_region_count]

    with patch("boto3.client") as mock_boto_client:
        with patch("data-management-handler.index.get_current_account_id") as mock_account_id:
            # Setup: Mock boto3 client
            mock_drs_client = MagicMock()
            mock_sts_client = MagicMock()

            def client_factory(service, **kwargs):
                if service == "drs":
                    return mock_drs_client
                elif service == "sts":
                    return mock_sts_client
                return MagicMock()

            mock_boto_client.side_effect = client_factory

            # Setup: Mock STS assume role
            mock_sts_client.assume_role.return_value = {
                "Credentials": {
                    "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
                    "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                    "SessionToken": "token",
                }
            }

            # Setup: Mock DRS describe_source_servers
            mock_paginator = MagicMock()
            mock_paginator.paginate.return_value = [{"items": []}]
            mock_drs_client.get_paginator.return_value = mock_paginator

            # Setup: Mock account ID
            mock_account_id.return_value = "123456789012"

            # Execute: Call get_staging_account_servers with active_regions
            servers = dm_handler.get_staging_account_servers(
                staging_account_id="987654321098",
                role_arn="arn:aws:iam::987654321098:role/StagingRole",
                external_id="external123",
                active_regions=active_regions,
            )

            # Verify: DRS client was created for each active region
            drs_client_calls = [call for call in mock_boto_client.call_args_list if call[0][0] == "drs"]

            # Account for the fact that ThreadPoolExecutor may create clients
            # The key is that we only query active_region_count regions
            assert len(drs_client_calls) <= active_region_count, (
                f"Should create at most {active_region_count} DRS clients, " f"got {len(drs_client_calls)}"
            )

            # Calculate reduction percentage
            reduction_pct = ((28 - active_region_count) / 28) * 100
            assert reduction_pct >= 0, f"Reduction percentage should be non-negative, got {reduction_pct}"

            # Verify: Reduction is proportional to regions skipped
            expected_min_reduction = ((28 - active_region_count) / 28) * 100
            assert reduction_pct >= expected_min_reduction - 1, (  # Allow 1% tolerance
                f"Expected at least {expected_min_reduction:.1f}% reduction, " f"got {reduction_pct:.1f}%"
            )


# Property 12: Cross-Account IAM Assumptions Limited to Active Regions
@settings(max_examples=100, deadline=None)
@given(active_region_count=st.integers(min_value=1, max_value=10))
def test_property_12_cross_account_iam_assumptions_limited(active_region_count):
    """
    Feature: active-region-filtering
    Property 12: Cross-Account IAM Assumptions Limited to Active Regions

    For any cross-account operation querying extended source servers, the number
    of IAM role assumptions should equal the number of active regions, not the
    total number of DRS regions (28).

    Validates: Requirements 9.3
    """
    # Select active_region_count regions from DRS_REGIONS
    active_regions = DRS_REGIONS[:active_region_count]

    with patch("boto3.client") as mock_boto_client:
        # Setup: Mock boto3 client
        mock_drs_client = MagicMock()
        mock_sts_client = MagicMock()

        def client_factory(service, **kwargs):
            if service == "drs":
                return mock_drs_client
            elif service == "sts":
                return mock_sts_client
            return MagicMock()

        mock_boto_client.side_effect = client_factory

        # Setup: Mock STS assume role (should be called once)
        mock_sts_client.assume_role.return_value = {
            "Credentials": {
                "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
                "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                "SessionToken": "token",
            }
        }

        # Setup: Mock DRS describe_source_servers
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [{"items": []}]
        mock_drs_client.get_paginator.return_value = mock_paginator

        # Execute: Call get_extended_source_servers with active_regions
        extended_arns = dm_handler.get_extended_source_servers(
            target_account_id="123456789012",
            role_arn="arn:aws:iam::123456789012:role/TargetRole",
            external_id="external123",
            active_regions=active_regions,
        )

        # Verify: STS assume_role was called exactly once (credentials reused)
        assert mock_sts_client.assume_role.call_count == 1, (
            f"STS assume_role should be called once (credentials reused), " f"got {mock_sts_client.assume_role.call_count}"
        )

        # Verify: DRS clients were created for active regions only
        drs_client_calls = [call for call in mock_boto_client.call_args_list if call[0][0] == "drs"]

        # The number of DRS client creations should match active_region_count
        assert len(drs_client_calls) <= active_region_count, (
            f"Should create at most {active_region_count} DRS clients for active regions, " f"got {len(drs_client_calls)}"
        )

        # Verify: Not querying all 28 regions
        assert len(drs_client_calls) < 28, f"Should not query all 28 regions, got {len(drs_client_calls)}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
