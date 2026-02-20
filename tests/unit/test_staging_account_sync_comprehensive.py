"""
Comprehensive Tests for Critical Staging Account Sync Functions

Tests the core staging account sync functions to ensure they work correctly:
- handle_sync_staging_accounts()
- auto_extend_staging_servers()
- extend_source_server()
- get_staging_account_servers()
- get_extended_source_servers()

These are critical functions that must work reliably for production use.
"""

import importlib
import json
import os
import sys
from typing import Dict, List
from unittest.mock import MagicMock, Mock, patch, call

import pytest
from botocore.exceptions import ClientError

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

# Import shared modules for patching
from shared import active_region_filter, inventory_query


class TestHandleSyncStagingAccounts:
    """Test handle_sync_staging_accounts() function."""

    def test_successful_sync_with_active_regions(self):
        """Test successful staging account sync with active region filtering."""
        active_regions = ["us-east-1", "us-west-2"]
        target_accounts = [
            {
                "accountId": "123456789012",
                "accountName": "Target Account",
                "roleArn": "arn:aws:iam::123456789012:role/DRSRole",
                "externalId": "external123",
                "isCurrentAccount": False,
                "stagingAccounts": [
                    {
                        "accountId": "987654321098",
                        "accountName": "Staging Account",
                        "roleArn": "arn:aws:iam::987654321098:role/StagingRole",
                        "externalId": "staging123",
                    }
                ],
            }
        ]

        with patch.object(active_region_filter, "get_active_regions") as mock_get_active:
            with patch.object(dm_handler, "get_target_accounts_table") as mock_table:
                with patch.object(dm_handler, "auto_extend_staging_servers") as mock_extend:
                    # Setup mocks
                    mock_get_active.return_value = active_regions
                    mock_table.return_value.scan.return_value = {"Items": target_accounts}
                    mock_extend.return_value = {
                        "totalAccounts": 1,
                        "accountsProcessed": 1,
                        "serversExtended": 2,
                        "serversFailed": 0,
                        "details": [],
                    }

                    # Execute
                    result = dm_handler.handle_sync_staging_accounts()

                    # Verify
                    assert result["statusCode"] == 200
                    body = json.loads(result["body"])  # Parse JSON string
                    assert body["totalAccounts"] == 1
                    assert body["serversExtended"] == 2
                    assert "timestamp" in body

                    # Verify active regions were used
                    mock_extend.assert_called_once()
                    call_args = mock_extend.call_args[0]
                    assert call_args[1] == active_regions

    def test_fallback_to_all_regions_when_table_empty(self):
        """Test fallback to all DRS regions when region status table is empty."""
        with patch.object(active_region_filter, "get_active_regions") as mock_get_active:
            with patch.object(dm_handler, "get_target_accounts_table") as mock_table:
                with patch.object(dm_handler, "auto_extend_staging_servers") as mock_extend:
                    # Setup: Empty active regions triggers fallback
                    mock_get_active.return_value = []
                    mock_table.return_value.scan.return_value = {"Items": []}
                    mock_extend.return_value = {
                        "totalAccounts": 0,
                        "accountsProcessed": 0,
                        "serversExtended": 0,
                        "serversFailed": 0,
                        "details": [],
                    }

                    # Execute
                    result = dm_handler.handle_sync_staging_accounts()

                    # Verify fallback to all regions
                    assert result["statusCode"] == 200
                    body = json.loads(result["body"])  # Parse JSON string
                    call_args = mock_extend.call_args[0]
                    assert call_args[1] == DRS_REGIONS

    def test_handles_pagination_of_target_accounts(self):
        """Test that pagination of target accounts is handled correctly."""
        accounts_page1 = [{"accountId": "111111111111", "accountName": "Account 1", "isCurrentAccount": False}]
        accounts_page2 = [{"accountId": "222222222222", "accountName": "Account 2", "isCurrentAccount": False}]

        with patch.object(active_region_filter, "get_active_regions") as mock_get_active:
            with patch.object(dm_handler, "get_target_accounts_table") as mock_table:
                with patch.object(dm_handler, "auto_extend_staging_servers") as mock_extend:
                    # Setup: Paginated responses
                    mock_get_active.return_value = ["us-east-1"]
                    mock_table.return_value.scan.side_effect = [
                        {"Items": accounts_page1, "LastEvaluatedKey": {"accountId": "111111111111"}},
                        {"Items": accounts_page2},
                    ]
                    mock_extend.return_value = {
                        "totalAccounts": 2,
                        "accountsProcessed": 0,
                        "serversExtended": 0,
                        "serversFailed": 0,
                        "details": [],
                    }

                    # Execute
                    result = dm_handler.handle_sync_staging_accounts()

                    # Verify both pages were retrieved
                    assert result["statusCode"] == 200
                    body = json.loads(result["body"])  # Parse JSON string
                    assert mock_table.return_value.scan.call_count == 2
                    # Verify all accounts were passed to auto_extend
                    call_args = mock_extend.call_args[0]
                    assert len(call_args[0]) == 2

    def test_handles_errors_gracefully(self):
        """Test that errors are handled gracefully and returned as 500."""
        with patch.object(active_region_filter, "get_active_regions") as mock_get_active:
            # Setup: Simulate error
            mock_get_active.side_effect = Exception("DynamoDB connection failed")

            # Execute
            result = dm_handler.handle_sync_staging_accounts()

            # Verify error response
            assert result["statusCode"] == 500
            body = json.loads(result["body"])  # Parse JSON string
            assert "error" in body


class TestAutoExtendStagingServers:
    """Test auto_extend_staging_servers() function."""

    def test_extends_new_servers_from_staging(self):
        """Test that new servers from staging accounts are extended to target."""
        active_regions = ["us-east-1"]
        target_accounts = [
            {
                "accountId": "123456789012",
                "accountName": "Target",
                "roleArn": "arn:aws:iam::123456789012:role/DRSRole",
                "externalId": "ext123",
                "isCurrentAccount": False,
                "stagingAccounts": [
                    {
                        "accountId": "987654321098",
                        "accountName": "Staging",
                        "roleArn": "arn:aws:iam::987654321098:role/StagingRole",
                        "externalId": "stg123",
                    }
                ],
            }
        ]

        staging_servers = [
            {
                "sourceServerID": "s-1234567890abcdef0",
                "arn": "arn:aws:drs:us-east-1:987654321098:source-server/s-1234567890abcdef0",
            }
        ]

        with patch.object(dm_handler, "get_extended_source_servers") as mock_get_extended:
            with patch.object(dm_handler, "get_staging_account_servers") as mock_get_staging:
                with patch.object(dm_handler, "extend_source_server") as mock_extend:
                    # Setup: No existing extended servers, one staging server
                    mock_get_extended.return_value = set()
                    mock_get_staging.return_value = staging_servers
                    mock_extend.return_value = None

                    # Execute
                    result = dm_handler.auto_extend_staging_servers(target_accounts, active_regions)

                    # Verify
                    assert result["serversExtended"] == 1
                    assert result["serversFailed"] == 0
                    assert result["accountsProcessed"] == 1
                    mock_extend.assert_called_once()

    def test_skips_already_extended_servers(self):
        """Test that servers already extended are skipped."""
        active_regions = ["us-east-1"]
        server_arn = "arn:aws:drs:us-east-1:987654321098:source-server/s-1234567890abcdef0"
        target_accounts = [
            {
                "accountId": "123456789012",
                "accountName": "Target",
                "roleArn": "arn:aws:iam::123456789012:role/DRSRole",
                "externalId": "ext123",
                "isCurrentAccount": False,
                "stagingAccounts": [
                    {
                        "accountId": "987654321098",
                        "accountName": "Staging",
                        "roleArn": "arn:aws:iam::987654321098:role/StagingRole",
                        "externalId": "stg123",
                    }
                ],
            }
        ]

        staging_servers = [{"sourceServerID": "s-1234567890abcdef0", "arn": server_arn}]

        with patch.object(dm_handler, "get_extended_source_servers") as mock_get_extended:
            with patch.object(dm_handler, "get_staging_account_servers") as mock_get_staging:
                with patch.object(dm_handler, "extend_source_server") as mock_extend:
                    # Setup: Server already extended
                    mock_get_extended.return_value = {server_arn}
                    mock_get_staging.return_value = staging_servers

                    # Execute
                    result = dm_handler.auto_extend_staging_servers(target_accounts, active_regions)

                    # Verify: No extension attempted
                    assert result["serversExtended"] == 0
                    mock_extend.assert_not_called()

    def test_handles_extend_failures(self):
        """Test that extend failures are counted and don't stop processing."""
        active_regions = ["us-east-1"]
        target_accounts = [
            {
                "accountId": "123456789012",
                "accountName": "Target",
                "roleArn": "arn:aws:iam::123456789012:role/DRSRole",
                "externalId": "ext123",
                "isCurrentAccount": False,
                "stagingAccounts": [
                    {
                        "accountId": "987654321098",
                        "accountName": "Staging",
                        "roleArn": "arn:aws:iam::987654321098:role/StagingRole",
                        "externalId": "stg123",
                    }
                ],
            }
        ]

        staging_servers = [
            {
                "sourceServerID": "s-1234567890abcdef0",
                "arn": "arn:aws:drs:us-east-1:987654321098:source-server/s-1234567890abcdef0",
            }
        ]

        with patch.object(dm_handler, "get_extended_source_servers") as mock_get_extended:
            with patch.object(dm_handler, "get_staging_account_servers") as mock_get_staging:
                with patch.object(dm_handler, "extend_source_server") as mock_extend:
                    # Setup: Extend fails
                    mock_get_extended.return_value = set()
                    mock_get_staging.return_value = staging_servers
                    mock_extend.side_effect = Exception("DRS API error")

                    # Execute
                    result = dm_handler.auto_extend_staging_servers(target_accounts, active_regions)

                    # Verify: Failure counted
                    assert result["serversExtended"] == 0
                    assert result["serversFailed"] == 1

    def test_skips_accounts_without_staging_accounts(self):
        """Test that accounts without staging accounts are skipped."""
        active_regions = ["us-east-1"]
        target_accounts = [
            {
                "accountId": "123456789012",
                "accountName": "Target",
                "roleArn": "arn:aws:iam::123456789012:role/DRSRole",
                "isCurrentAccount": False,
                "stagingAccounts": [],  # No staging accounts
            }
        ]

        with patch.object(dm_handler, "get_extended_source_servers") as mock_get_extended:
            with patch.object(dm_handler, "get_staging_account_servers") as mock_get_staging:
                # Execute
                result = dm_handler.auto_extend_staging_servers(target_accounts, active_regions)

                # Verify: No processing
                assert result["accountsProcessed"] == 0
                mock_get_extended.assert_not_called()
                mock_get_staging.assert_not_called()

    def test_skips_current_account(self):
        """Test that current account is skipped."""
        active_regions = ["us-east-1"]
        target_accounts = [
            {
                "accountId": "123456789012",
                "accountName": "Current",
                "isCurrentAccount": True,
                "stagingAccounts": [{"accountId": "987654321098"}],
            }
        ]

        with patch.object(dm_handler, "get_extended_source_servers") as mock_get_extended:
            # Execute
            result = dm_handler.auto_extend_staging_servers(target_accounts, active_regions)

            # Verify: Skipped
            assert result["accountsProcessed"] == 0
            mock_get_extended.assert_not_called()


class TestExtendSourceServer:
    """Test extend_source_server() function."""

    def test_extends_server_successfully(self):
        """Test successful server extension."""
        server_arn = "arn:aws:drs:us-east-1:987654321098:source-server/s-1234567890abcdef0"

        with patch.object(dm_handler, "create_drs_client") as mock_create_client:
            # Setup
            mock_drs_client = MagicMock()
            mock_create_client.return_value = mock_drs_client

            # Execute
            dm_handler.extend_source_server(
                target_account_id="123456789012",
                target_role_arn="arn:aws:iam::123456789012:role/DRSRole",
                target_external_id="ext123",
                staging_server_arn=server_arn,
            )

            # Verify
            mock_create_client.assert_called_once()
            mock_drs_client.create_extended_source_server.assert_called_once_with(sourceServerArn=server_arn)

    def test_extracts_region_from_arn(self):
        """Test that region is correctly extracted from server ARN."""
        server_arn = "arn:aws:drs:eu-west-1:987654321098:source-server/s-1234567890abcdef0"

        with patch.object(dm_handler, "create_drs_client") as mock_create_client:
            # Setup
            mock_drs_client = MagicMock()
            mock_create_client.return_value = mock_drs_client

            # Execute
            dm_handler.extend_source_server(
                target_account_id="123456789012",
                target_role_arn="arn:aws:iam::123456789012:role/DRSRole",
                target_external_id="ext123",
                staging_server_arn=server_arn,
            )

            # Verify region was extracted correctly
            call_args = mock_create_client.call_args[0]
            assert call_args[0] == "eu-west-1"

    def test_raises_error_for_invalid_arn(self):
        """Test that invalid ARN format raises ValueError."""
        invalid_arn = "invalid-arn-format"

        with pytest.raises(ValueError, match="Invalid server ARN format"):
            dm_handler.extend_source_server(
                target_account_id="123456789012",
                target_role_arn="arn:aws:iam::123456789012:role/DRSRole",
                target_external_id="ext123",
                staging_server_arn=invalid_arn,
            )


class TestGetStagingAccountServers:
    """Test get_staging_account_servers() function."""

    def test_uses_inventory_database_when_fresh(self):
        """Test that inventory database is used when data is fresh."""
        active_regions = ["us-east-1", "us-west-2"]
        servers = [{"sourceServerID": "s-123", "arn": "arn:aws:drs:us-east-1:123:source-server/s-123"}]

        with patch.object(inventory_query, "is_inventory_fresh") as mock_is_fresh:
            with patch.object(inventory_query, "query_inventory_by_staging_account") as mock_query:
                # Setup: Fresh inventory
                mock_is_fresh.return_value = True
                mock_query.return_value = servers

                # Execute
                result = dm_handler.get_staging_account_servers(
                    staging_account_id="987654321098",
                    role_arn="arn:aws:iam::987654321098:role/StagingRole",
                    external_id="ext123",
                    active_regions=active_regions,
                )

                # Verify
                assert result == servers
                mock_query.assert_called_once_with(staging_account_id="987654321098", regions=active_regions)

    def test_falls_back_to_drs_api_when_inventory_stale(self):
        """Test fallback to DRS API when inventory is stale."""
        active_regions = ["us-east-1"]

        with patch.object(inventory_query, "is_inventory_fresh") as mock_is_fresh:
            with patch.object(inventory_query, "query_inventory_by_staging_account") as mock_query:
                with patch("boto3.client") as mock_boto_client:
                    with patch.object(dm_handler, "get_current_account_id") as mock_account_id:
                        # Setup: Stale inventory
                        mock_is_fresh.return_value = False
                        mock_account_id.return_value = "123456789012"

                        # Setup: Mock DRS client
                        mock_drs_client = MagicMock()
                        mock_sts_client = MagicMock()

                        def client_factory(service, **kwargs):
                            if service == "drs":
                                return mock_drs_client
                            elif service == "sts":
                                return mock_sts_client
                            return MagicMock()

                        mock_boto_client.side_effect = client_factory

                        # Setup: Mock STS and DRS responses
                        mock_sts_client.assume_role.return_value = {
                            "Credentials": {
                                "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
                                "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                                "SessionToken": "token",
                            }
                        }
                        mock_paginator = MagicMock()
                        mock_paginator.paginate.return_value = [{"items": [{"sourceServerID": "s-123"}]}]
                        mock_drs_client.get_paginator.return_value = mock_paginator

                        # Execute
                        result = dm_handler.get_staging_account_servers(
                            staging_account_id="987654321098",
                            role_arn="arn:aws:iam::987654321098:role/StagingRole",
                            external_id="ext123",
                            active_regions=active_regions,
                        )

                        # Verify: DRS API was used
                        assert len(result) == 1
                        assert result[0]["sourceServerID"] == "s-123"

    def test_handles_uninitialized_account_exception(self):
        """Test that UninitializedAccountException is handled gracefully."""
        active_regions = ["us-east-1"]

        with patch.object(inventory_query, "is_inventory_fresh") as mock_is_fresh:
            with patch("boto3.client") as mock_boto_client:
                with patch.object(dm_handler, "get_current_account_id") as mock_account_id:
                    # Setup
                    mock_is_fresh.return_value = False
                    mock_account_id.return_value = "123456789012"

                    mock_drs_client = MagicMock()
                    mock_sts_client = MagicMock()

                    def client_factory(service, **kwargs):
                        if service == "drs":
                            return mock_drs_client
                        elif service == "sts":
                            return mock_sts_client
                        return MagicMock()

                    mock_boto_client.side_effect = client_factory

                    mock_sts_client.assume_role.return_value = {
                        "Credentials": {
                            "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
                            "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                            "SessionToken": "token",
                        }
                    }

                    # Setup: DRS API raises UninitializedAccountException
                    mock_paginator = MagicMock()
                    error_response = {"Error": {"Code": "UninitializedAccountException"}}
                    mock_paginator.paginate.side_effect = ClientError(error_response, "describe_source_servers")
                    mock_drs_client.get_paginator.return_value = mock_paginator

                    # Execute
                    result = dm_handler.get_staging_account_servers(
                        staging_account_id="987654321098",
                        role_arn="arn:aws:iam::987654321098:role/StagingRole",
                        external_id="ext123",
                        active_regions=active_regions,
                    )

                    # Verify: Empty list returned
                    assert result == []


class TestGetExtendedSourceServers:
    """Test get_extended_source_servers() function."""

    def test_returns_extended_server_arns(self):
        """Test that extended source server ARNs are returned."""
        active_regions = ["us-east-1"]
        staging_arn = "arn:aws:drs:us-east-1:987654321098:source-server/s-staging123"

        with patch("boto3.client") as mock_boto_client:
            # Setup
            mock_drs_client = MagicMock()
            mock_sts_client = MagicMock()

            def client_factory(service, **kwargs):
                if service == "drs":
                    return mock_drs_client
                elif service == "sts":
                    return mock_sts_client
                return MagicMock()

            mock_boto_client.side_effect = client_factory

            mock_sts_client.assume_role.return_value = {
                "Credentials": {
                    "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
                    "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                    "SessionToken": "token",
                }
            }

            # Setup: Mock extended server
            mock_paginator = MagicMock()
            mock_paginator.paginate.return_value = [
                {
                    "items": [
                        {
                            "sourceServerID": "s-target123",
                            "stagingArea": {
                                "stagingAccountID": "987654321098",
                                "stagingSourceServerArn": staging_arn,
                            },
                        }
                    ]
                }
            ]
            mock_drs_client.get_paginator.return_value = mock_paginator

            # Execute
            result = dm_handler.get_extended_source_servers(
                target_account_id="123456789012",
                role_arn="arn:aws:iam::123456789012:role/DRSRole",
                external_id="ext123",
                active_regions=active_regions,
            )

            # Verify
            assert staging_arn in result
            assert len(result) == 1

    def test_filters_out_non_extended_servers(self):
        """Test that servers from same account are filtered out."""
        active_regions = ["us-east-1"]

        with patch("boto3.client") as mock_boto_client:
            # Setup
            mock_drs_client = MagicMock()
            mock_sts_client = MagicMock()

            def client_factory(service, **kwargs):
                if service == "drs":
                    return mock_drs_client
                elif service == "sts":
                    return mock_sts_client
                return MagicMock()

            mock_boto_client.side_effect = client_factory

            mock_sts_client.assume_role.return_value = {
                "Credentials": {
                    "AccessKeyId": "AKIAIOSFODNN7EXAMPLE",
                    "SecretAccessKey": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
                    "SessionToken": "token",
                }
            }

            # Setup: Server from same account (not extended)
            mock_paginator = MagicMock()
            mock_paginator.paginate.return_value = [
                {
                    "items": [
                        {
                            "sourceServerID": "s-local123",
                            "stagingArea": {
                                "stagingAccountID": "123456789012",  # Same as target
                                "stagingSourceServerArn": "arn:aws:drs:us-east-1:123456789012:source-server/s-local123",
                            },
                        }
                    ]
                }
            ]
            mock_drs_client.get_paginator.return_value = mock_paginator

            # Execute
            result = dm_handler.get_extended_source_servers(
                target_account_id="123456789012",
                role_arn="arn:aws:iam::123456789012:role/DRSRole",
                external_id="ext123",
                active_regions=active_regions,
            )

            # Verify: Empty set (server filtered out)
            assert len(result) == 0

    def test_handles_assume_role_failure(self):
        """Test that assume role failures are handled gracefully."""
        active_regions = ["us-east-1"]

        with patch("boto3.client") as mock_boto_client:
            # Setup
            mock_sts_client = MagicMock()
            mock_boto_client.return_value = mock_sts_client

            # Setup: Assume role fails
            mock_sts_client.assume_role.side_effect = Exception("Access denied")

            # Execute
            result = dm_handler.get_extended_source_servers(
                target_account_id="123456789012",
                role_arn="arn:aws:iam::123456789012:role/DRSRole",
                external_id="ext123",
                active_regions=active_regions,
            )

            # Verify: Empty set returned
            assert len(result) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
