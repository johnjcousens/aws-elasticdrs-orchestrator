"""
Unit tests for recovery instance sync shared utility.

Feature: recovery-instance-sync
Tests for lambda/shared/recovery_instance_sync.py functions.

Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5
"""

import os
import sys
from datetime import datetime, timezone
from unittest.mock import MagicMock, call, patch

import pytest
from botocore.exceptions import ClientError

# Add lambda directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda"))

import shared.recovery_instance_sync as sync_module
from shared.recovery_instance_sync import (
    RecoveryInstanceSyncError,
    RecoveryInstanceSyncTimeoutError,
    RecoveryInstanceSyncValidationError,
    enrich_with_ec2_details,
    find_source_execution,
    get_recovery_instance_sync_status,
    get_recovery_instances_for_region,
    sync_all_recovery_instances,
    sync_recovery_instances_for_account,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_sync_module_globals():
    """Reset module-level cached resources before each test."""
    sync_module._dynamodb = None
    sync_module._recovery_instances_table = None
    sync_module._execution_history_table = None
    sync_module._target_accounts_table = None
    yield
    sync_module._dynamodb = None
    sync_module._recovery_instances_table = None
    sync_module._execution_history_table = None
    sync_module._target_accounts_table = None


@pytest.fixture(autouse=True)
def set_sync_env_vars(monkeypatch):
    """Set required environment variables for sync tests."""
    monkeypatch.setenv("RECOVERY_INSTANCES_CACHE_TABLE", "test-recovery-instances-table")
    monkeypatch.setenv("EXECUTION_HISTORY_TABLE", "test-execution-history-table")
    monkeypatch.setenv("TARGET_ACCOUNTS_TABLE", "test-target-accounts-table")
    # Re-read env vars since module reads them at import time
    sync_module.RECOVERY_INSTANCES_CACHE_TABLE = "test-recovery-instances-table"
    sync_module.EXECUTION_HISTORY_TABLE = "test-execution-history-table"
    sync_module.TARGET_ACCOUNTS_TABLE = "test-target-accounts-table"


@pytest.fixture
def mock_dynamodb_table():
    """Create a mock DynamoDB table."""
    mock_table = MagicMock()
    mock_batch_writer = MagicMock()
    mock_table.batch_writer.return_value.__enter__ = MagicMock(return_value=mock_batch_writer)
    mock_table.batch_writer.return_value.__exit__ = MagicMock(return_value=False)
    return mock_table, mock_batch_writer


def _make_client_error(code: str = "AccessDeniedException", message: str = "Access denied") -> ClientError:
    """Helper to create a ClientError."""
    return ClientError({"Error": {"Code": code, "Message": message}}, "TestOperation")


# ---------------------------------------------------------------------------
# 11.1 Test sync_all_recovery_instances()
# ---------------------------------------------------------------------------

class TestSyncAllRecoveryInstances:
    """Tests for sync_all_recovery_instances().

    Validates: Requirements 1.3 (background sync)
    """

    @patch("shared.recovery_instance_sync._get_recovery_instances_table")
    @patch("shared.recovery_instance_sync.find_source_execution")
    @patch("shared.recovery_instance_sync.enrich_with_ec2_details")
    @patch("shared.recovery_instance_sync.get_recovery_instances_for_region")
    @patch("shared.recovery_instance_sync._get_target_accounts")
    def test_sync_all_happy_path(
        self, mock_accounts, mock_get_instances, mock_enrich, mock_find_exec, mock_get_table
    ):
        """Test successful sync across multiple accounts and regions."""
        mock_accounts.return_value = [
            {"accountId": "111111111111", "regions": ["us-east-1", "us-west-2"], "accountContext": {}},
        ]
        mock_get_instances.return_value = [
            {
                "sourceServerId": "s-abc123",
                "recoveryInstanceId": "ri-abc123",
                "ec2InstanceId": "i-abc123",
                "ec2InstanceState": "running",
                "region": "us-east-1",
                "accountId": "111111111111",
                "sourceServerName": "web-01",
                "launchTime": "2025-01-01T00:00:00Z",
            },
        ]
        mock_enrich.return_value = {
            "Name": "Recovery of web-01",
            "PrivateIpAddress": "10.0.1.1",
            "PublicIpAddress": "54.1.2.3",
            "InstanceType": "t3.medium",
            "LaunchTime": "2025-01-01T00:00:00Z",
        }
        mock_find_exec.return_value = {"executionId": "exec-001", "planName": "DR Plan"}

        mock_table = MagicMock()
        mock_batch = MagicMock()
        mock_table.batch_writer.return_value.__enter__ = MagicMock(return_value=mock_batch)
        mock_table.batch_writer.return_value.__exit__ = MagicMock(return_value=False)
        mock_get_table.return_value = mock_table

        result = sync_all_recovery_instances()

        assert result["instancesUpdated"] == 2  # 1 instance * 2 regions
        assert result["regionsScanned"] == 2
        assert result["errors"] == []
        assert mock_batch.put_item.call_count == 2

    @patch("shared.recovery_instance_sync._get_recovery_instances_table")
    @patch("shared.recovery_instance_sync.find_source_execution")
    @patch("shared.recovery_instance_sync.enrich_with_ec2_details")
    @patch("shared.recovery_instance_sync.get_recovery_instances_for_region")
    @patch("shared.recovery_instance_sync._get_target_accounts")
    def test_sync_all_no_accounts(
        self, mock_accounts, mock_get_instances, mock_enrich, mock_find_exec, mock_get_table
    ):
        """Test sync with no target accounts returns zero instances."""
        mock_accounts.return_value = []

        result = sync_all_recovery_instances()

        assert result["instancesUpdated"] == 0
        assert result["regionsScanned"] == 0
        assert result["errors"] == []
        mock_get_instances.assert_not_called()

    @patch("shared.recovery_instance_sync._get_recovery_instances_table")
    @patch("shared.recovery_instance_sync.find_source_execution")
    @patch("shared.recovery_instance_sync.enrich_with_ec2_details")
    @patch("shared.recovery_instance_sync.get_recovery_instances_for_region")
    @patch("shared.recovery_instance_sync._get_target_accounts")
    def test_sync_all_region_failure_continues(
        self, mock_accounts, mock_get_instances, mock_enrich, mock_find_exec, mock_get_table
    ):
        """Test that a region failure doesn't stop processing other regions."""
        mock_accounts.return_value = [
            {"accountId": "111111111111", "regions": ["us-east-1", "us-west-2"], "accountContext": {}},
        ]
        mock_get_instances.side_effect = [
            Exception("DRS API timeout"),
            [
                {
                    "sourceServerId": "s-def456",
                    "recoveryInstanceId": "ri-def456",
                    "ec2InstanceId": "i-def456",
                    "ec2InstanceState": "running",
                    "region": "us-west-2",
                    "accountId": "111111111111",
                    "launchTime": "2025-01-01T00:00:00Z",
                },
            ],
        ]
        mock_enrich.return_value = {"Name": "test", "InstanceType": "t3.medium"}
        mock_find_exec.return_value = {}

        mock_table = MagicMock()
        mock_batch = MagicMock()
        mock_table.batch_writer.return_value.__enter__ = MagicMock(return_value=mock_batch)
        mock_table.batch_writer.return_value.__exit__ = MagicMock(return_value=False)
        mock_get_table.return_value = mock_table

        result = sync_all_recovery_instances()

        assert result["instancesUpdated"] == 1
        assert result["regionsScanned"] == 2
        assert len(result["errors"]) == 1
        assert "DRS API timeout" in result["errors"][0]

    @patch("shared.recovery_instance_sync._get_recovery_instances_table")
    @patch("shared.recovery_instance_sync.find_source_execution")
    @patch("shared.recovery_instance_sync.enrich_with_ec2_details")
    @patch("shared.recovery_instance_sync.get_recovery_instances_for_region")
    @patch("shared.recovery_instance_sync._get_target_accounts")
    def test_sync_all_enrichment_failure_continues(
        self, mock_accounts, mock_get_instances, mock_enrich, mock_find_exec, mock_get_table
    ):
        """Test that enrichment failure for one instance doesn't stop others."""
        mock_accounts.return_value = [
            {"accountId": "111111111111", "regions": ["us-east-1"], "accountContext": {}},
        ]
        mock_get_instances.return_value = [
            {
                "sourceServerId": "s-abc",
                "recoveryInstanceId": "ri-abc",
                "ec2InstanceId": "i-abc",
                "ec2InstanceState": "running",
                "region": "us-east-1",
                "accountId": "111111111111",
            },
            {
                "sourceServerId": "s-def",
                "recoveryInstanceId": "ri-def",
                "ec2InstanceId": "i-def",
                "ec2InstanceState": "running",
                "region": "us-east-1",
                "accountId": "111111111111",
            },
        ]
        # First enrichment fails, second succeeds
        mock_enrich.side_effect = [Exception("EC2 error"), {"Name": "ok", "InstanceType": "t3.small"}]
        mock_find_exec.return_value = {}

        mock_table = MagicMock()
        mock_batch = MagicMock()
        mock_table.batch_writer.return_value.__enter__ = MagicMock(return_value=mock_batch)
        mock_table.batch_writer.return_value.__exit__ = MagicMock(return_value=False)
        mock_get_table.return_value = mock_table

        result = sync_all_recovery_instances()

        # One enrichment failed, one succeeded
        assert result["instancesUpdated"] == 1
        assert len(result["errors"]) == 1
        assert "EC2 error" in result["errors"][0]

    @patch("shared.recovery_instance_sync._get_recovery_instances_table")
    @patch("shared.recovery_instance_sync.find_source_execution")
    @patch("shared.recovery_instance_sync.enrich_with_ec2_details")
    @patch("shared.recovery_instance_sync.get_recovery_instances_for_region")
    @patch("shared.recovery_instance_sync._get_target_accounts")
    def test_sync_all_dynamodb_write_failure(
        self, mock_accounts, mock_get_instances, mock_enrich, mock_find_exec, mock_get_table
    ):
        """Test DynamoDB write failure is captured in errors."""
        mock_accounts.return_value = [
            {"accountId": "111111111111", "regions": ["us-east-1"], "accountContext": {}},
        ]
        mock_get_instances.return_value = [
            {
                "sourceServerId": "s-abc",
                "recoveryInstanceId": "ri-abc",
                "ec2InstanceId": "i-abc",
                "ec2InstanceState": "running",
                "region": "us-east-1",
                "accountId": "111111111111",
            },
        ]
        mock_enrich.return_value = {"Name": "test", "InstanceType": "t3.medium"}
        mock_find_exec.return_value = {}

        mock_table = MagicMock()
        mock_table.batch_writer.side_effect = Exception("DynamoDB write error")
        mock_get_table.return_value = mock_table

        result = sync_all_recovery_instances()

        assert len(result["errors"]) == 1
        assert "DynamoDB" in result["errors"][0]

    @patch("shared.recovery_instance_sync._get_recovery_instances_table")
    @patch("shared.recovery_instance_sync.find_source_execution")
    @patch("shared.recovery_instance_sync.enrich_with_ec2_details")
    @patch("shared.recovery_instance_sync.get_recovery_instances_for_region")
    @patch("shared.recovery_instance_sync._get_target_accounts")
    def test_sync_all_writes_correct_fields(
        self, mock_accounts, mock_get_instances, mock_enrich, mock_find_exec, mock_get_table
    ):
        """Test that all required fields are written to DynamoDB."""
        mock_accounts.return_value = [
            {"accountId": "111111111111", "regions": ["us-east-1"], "accountContext": {}},
        ]
        mock_get_instances.return_value = [
            {
                "sourceServerId": "s-abc123",
                "recoveryInstanceId": "ri-abc123",
                "ec2InstanceId": "i-abc123",
                "ec2InstanceState": "running",
                "region": "us-east-1",
                "accountId": "111111111111",
                "sourceServerName": "web-01",
                "launchTime": "2025-01-01T00:00:00Z",
                "replicationStagingAccountId": "222222222222",
                "sourceVpcId": "vpc-abc",
                "sourceSubnetId": "subnet-abc",
                "sourceSecurityGroupIds": ["sg-111"],
                "sourceInstanceProfile": "arn:aws:iam::111111111111:instance-profile/MyRole",
            },
        ]
        mock_enrich.return_value = {
            "Name": "Recovery of web-01",
            "PrivateIpAddress": "10.0.1.1",
            "PublicIpAddress": "54.1.2.3",
            "InstanceType": "t3.medium",
            "LaunchTime": "2025-01-01T00:00:00Z",
        }
        mock_find_exec.return_value = {"executionId": "exec-001", "planName": "DR Plan"}

        mock_table = MagicMock()
        mock_batch = MagicMock()
        mock_table.batch_writer.return_value.__enter__ = MagicMock(return_value=mock_batch)
        mock_table.batch_writer.return_value.__exit__ = MagicMock(return_value=False)
        mock_get_table.return_value = mock_table

        sync_all_recovery_instances()

        written_item = mock_batch.put_item.call_args[1]["Item"]
        assert written_item["sourceServerId"] == "s-abc123"
        assert written_item["recoveryInstanceId"] == "ri-abc123"
        assert written_item["ec2InstanceId"] == "i-abc123"
        assert written_item["ec2InstanceState"] == "running"
        assert written_item["sourceServerName"] == "web-01"
        assert written_item["name"] == "Recovery of web-01"
        assert written_item["privateIp"] == "10.0.1.1"
        assert written_item["publicIp"] == "54.1.2.3"
        assert written_item["instanceType"] == "t3.medium"
        assert written_item["region"] == "us-east-1"
        assert written_item["accountId"] == "111111111111"
        assert written_item["sourceExecutionId"] == "exec-001"
        assert written_item["sourcePlanName"] == "DR Plan"
        assert "lastSyncTime" in written_item
        assert written_item["replicationStagingAccountId"] == "222222222222"
        assert written_item["sourceVpcId"] == "vpc-abc"
        assert written_item["sourceSubnetId"] == "subnet-abc"
        assert written_item["sourceSecurityGroupIds"] == ["sg-111"]
        assert written_item["sourceInstanceProfile"] == "arn:aws:iam::111111111111:instance-profile/MyRole"


# ---------------------------------------------------------------------------
# 11.2 Test sync_recovery_instances_for_account()
# ---------------------------------------------------------------------------

class TestSyncRecoveryInstancesForAccount:
    """Tests for sync_recovery_instances_for_account().

    Validates: Requirements 1.2 (wave completion sync)
    """

    @patch("shared.recovery_instance_sync._get_recovery_instances_table")
    @patch("shared.recovery_instance_sync.find_source_execution")
    @patch("shared.recovery_instance_sync.enrich_with_ec2_details")
    @patch("shared.recovery_instance_sync.get_recovery_instances_for_region")
    def test_single_account_sync_happy_path(self, mock_get_instances, mock_enrich, mock_find_exec, mock_get_table):
        """Test successful sync for a single account/region."""
        mock_get_instances.return_value = [
            {
                "sourceServerId": "s-abc",
                "recoveryInstanceId": "ri-abc",
                "ec2InstanceId": "i-abc",
                "ec2InstanceState": "running",
                "region": "us-east-2",
                "accountId": "111111111111",
                "sourceServerName": "app-01",
                "launchTime": "2025-02-01T12:00:00Z",
            },
        ]
        mock_enrich.return_value = {
            "Name": "Recovery of app-01",
            "PrivateIpAddress": "10.0.0.5",
            "PublicIpAddress": None,
            "InstanceType": "m5.large",
        }
        mock_find_exec.return_value = {"executionId": "exec-100", "planName": "App Recovery"}

        mock_table = MagicMock()
        mock_batch = MagicMock()
        mock_table.batch_writer.return_value.__enter__ = MagicMock(return_value=mock_batch)
        mock_table.batch_writer.return_value.__exit__ = MagicMock(return_value=False)
        mock_get_table.return_value = mock_table

        result = sync_recovery_instances_for_account("111111111111", "us-east-2")

        assert result["instancesUpdated"] == 1
        assert result["errors"] == []
        mock_batch.put_item.assert_called_once()

    @patch("shared.recovery_instance_sync.get_recovery_instances_for_region")
    def test_single_account_no_instances(self, mock_get_instances):
        """Test sync when no recovery instances exist."""
        mock_get_instances.return_value = []

        result = sync_recovery_instances_for_account("111111111111", "us-east-2")

        assert result["instancesUpdated"] == 0
        assert result["errors"] == []

    @patch("shared.recovery_instance_sync.get_recovery_instances_for_region")
    def test_single_account_drs_failure(self, mock_get_instances):
        """Test sync when DRS API call fails."""
        mock_get_instances.side_effect = RecoveryInstanceSyncError("DRS unavailable")

        result = sync_recovery_instances_for_account("111111111111", "us-east-2")

        assert result["instancesUpdated"] == 0
        assert len(result["errors"]) == 1
        assert "DRS unavailable" in result["errors"][0]

    @patch("shared.recovery_instance_sync._get_recovery_instances_table")
    @patch("shared.recovery_instance_sync.find_source_execution")
    @patch("shared.recovery_instance_sync.enrich_with_ec2_details")
    @patch("shared.recovery_instance_sync.get_recovery_instances_for_region")
    def test_single_account_partial_enrichment_failure(
        self, mock_get_instances, mock_enrich, mock_find_exec, mock_get_table
    ):
        """Test that enrichment failure for one instance doesn't block others."""
        mock_get_instances.return_value = [
            {
                "sourceServerId": "s-1",
                "recoveryInstanceId": "ri-1",
                "ec2InstanceId": "i-1",
                "ec2InstanceState": "running",
                "region": "us-east-2",
                "accountId": "111111111111",
            },
            {
                "sourceServerId": "s-2",
                "recoveryInstanceId": "ri-2",
                "ec2InstanceId": "i-2",
                "ec2InstanceState": "running",
                "region": "us-east-2",
                "accountId": "111111111111",
            },
        ]
        mock_enrich.side_effect = [Exception("EC2 error"), {"Name": "ok", "InstanceType": "t3.small"}]
        mock_find_exec.return_value = {}

        mock_table = MagicMock()
        mock_batch = MagicMock()
        mock_table.batch_writer.return_value.__enter__ = MagicMock(return_value=mock_batch)
        mock_table.batch_writer.return_value.__exit__ = MagicMock(return_value=False)
        mock_get_table.return_value = mock_table

        result = sync_recovery_instances_for_account("111111111111", "us-east-2")

        assert result["instancesUpdated"] == 1
        assert len(result["errors"]) == 1

    @patch("shared.recovery_instance_sync._get_recovery_instances_table")
    @patch("shared.recovery_instance_sync.find_source_execution")
    @patch("shared.recovery_instance_sync.enrich_with_ec2_details")
    @patch("shared.recovery_instance_sync.get_recovery_instances_for_region")
    def test_single_account_with_account_context(
        self, mock_get_instances, mock_enrich, mock_find_exec, mock_get_table
    ):
        """Test sync passes account_context for cross-account operations."""
        account_context = {
            "accountId": "222222222222",
            "assumeRoleName": "DRSCrossAccountRole",
            "externalId": "ext-123",
            "isCurrentAccount": False,
        }
        mock_get_instances.return_value = [
            {
                "sourceServerId": "s-cross",
                "recoveryInstanceId": "ri-cross",
                "ec2InstanceId": "i-cross",
                "ec2InstanceState": "running",
                "region": "us-west-2",
                "accountId": "222222222222",
                "accountContext": account_context,
            },
        ]
        mock_enrich.return_value = {"Name": "cross-acct", "InstanceType": "t3.micro"}
        mock_find_exec.return_value = {}

        mock_table = MagicMock()
        mock_batch = MagicMock()
        mock_table.batch_writer.return_value.__enter__ = MagicMock(return_value=mock_batch)
        mock_table.batch_writer.return_value.__exit__ = MagicMock(return_value=False)
        mock_get_table.return_value = mock_table

        result = sync_recovery_instances_for_account("222222222222", "us-west-2", account_context)

        assert result["instancesUpdated"] == 1
        mock_get_instances.assert_called_once_with("222222222222", "us-west-2", account_context)


# ---------------------------------------------------------------------------
# 11.3 Test get_recovery_instances_for_region() with pagination
# ---------------------------------------------------------------------------

class TestGetRecoveryInstancesForRegion:
    """Tests for get_recovery_instances_for_region().

    Validates: Requirements 1.3 (DRS API queries)
    """

    @patch("shared.recovery_instance_sync.boto3")
    def test_single_page_response(self, mock_boto3):
        """Test querying DRS with a single page of results."""
        mock_drs = MagicMock()
        mock_boto3.client.return_value = mock_drs
        mock_drs.describe_recovery_instances.return_value = {
            "items": [
                {
                    "sourceServerID": "s-abc",
                    "recoveryInstanceID": "ri-abc",
                    "ec2InstanceID": "i-abc",
                    "ec2InstanceState": "running",
                    "launchTime": "2025-01-01T00:00:00Z",
                },
            ],
        }
        mock_drs.describe_source_servers.return_value = {
            "items": [
                {
                    "sourceProperties": {"hostname": "web-01"},
                    "stagingArea": {"stagingAccountID": "222222222222"},
                },
            ],
        }

        result = get_recovery_instances_for_region("111111111111", "us-east-1")

        assert len(result) == 1
        assert result[0]["sourceServerId"] == "s-abc"
        assert result[0]["recoveryInstanceId"] == "ri-abc"
        assert result[0]["ec2InstanceId"] == "i-abc"
        assert result[0]["region"] == "us-east-1"
        assert result[0]["accountId"] == "111111111111"
        assert result[0]["sourceServerName"] == "web-01"
        assert result[0]["replicationStagingAccountId"] == "222222222222"

    @patch("shared.recovery_instance_sync.boto3")
    def test_paginated_response(self, mock_boto3):
        """Test querying DRS with multiple pages of results."""
        mock_drs = MagicMock()
        mock_boto3.client.return_value = mock_drs

        # First page has nextToken, second page does not
        mock_drs.describe_recovery_instances.side_effect = [
            {
                "items": [
                    {
                        "sourceServerID": "s-page1",
                        "recoveryInstanceID": "ri-page1",
                        "ec2InstanceID": "i-page1",
                        "ec2InstanceState": "running",
                    },
                ],
                "nextToken": "token-page2",
            },
            {
                "items": [
                    {
                        "sourceServerID": "s-page2",
                        "recoveryInstanceID": "ri-page2",
                        "ec2InstanceID": "i-page2",
                        "ec2InstanceState": "stopped",
                    },
                ],
            },
        ]
        mock_drs.describe_source_servers.return_value = {"items": []}

        result = get_recovery_instances_for_region("111111111111", "us-east-1")

        assert len(result) == 2
        assert result[0]["sourceServerId"] == "s-page1"
        assert result[1]["sourceServerId"] == "s-page2"
        assert mock_drs.describe_recovery_instances.call_count == 2

    @patch("shared.recovery_instance_sync.boto3")
    def test_empty_response(self, mock_boto3):
        """Test querying DRS with no recovery instances."""
        mock_drs = MagicMock()
        mock_boto3.client.return_value = mock_drs
        mock_drs.describe_recovery_instances.return_value = {"items": []}

        result = get_recovery_instances_for_region("111111111111", "us-east-1")

        assert result == []

    @patch("shared.recovery_instance_sync.boto3")
    def test_drs_client_error_raises_sync_error(self, mock_boto3):
        """Test that DRS ClientError is wrapped in RecoveryInstanceSyncError."""
        mock_drs = MagicMock()
        mock_boto3.client.return_value = mock_drs
        mock_drs.describe_recovery_instances.side_effect = _make_client_error(
            "UninitializedAccountException", "DRS not initialized"
        )

        with pytest.raises(RecoveryInstanceSyncError, match="DRS API error"):
            get_recovery_instances_for_region("111111111111", "us-east-1")

    @patch("shared.recovery_instance_sync.boto3")
    def test_source_server_lookup_failure_continues(self, mock_boto3):
        """Test that source server lookup failure doesn't block instance processing."""
        mock_drs = MagicMock()
        mock_boto3.client.return_value = mock_drs
        mock_drs.describe_recovery_instances.return_value = {
            "items": [
                {
                    "sourceServerID": "s-abc",
                    "recoveryInstanceID": "ri-abc",
                    "ec2InstanceID": "i-abc",
                    "ec2InstanceState": "running",
                },
            ],
        }
        mock_drs.describe_source_servers.side_effect = Exception("Source server lookup failed")

        result = get_recovery_instances_for_region("111111111111", "us-east-1")

        assert len(result) == 1
        assert result[0]["sourceServerId"] == "s-abc"
        # sourceServerName should not be set since lookup failed
        assert result[0].get("sourceServerName") is None

    @patch("shared.recovery_instance_sync.boto3")
    def test_extracts_source_infrastructure_fields(self, mock_boto3):
        """Test that source infrastructure fields are extracted from source server data."""
        mock_drs = MagicMock()
        mock_boto3.client.return_value = mock_drs
        mock_drs.describe_recovery_instances.return_value = {
            "items": [
                {
                    "sourceServerID": "s-infra",
                    "recoveryInstanceID": "ri-infra",
                    "ec2InstanceID": "i-infra",
                    "ec2InstanceState": "running",
                },
            ],
        }
        mock_drs.describe_source_servers.return_value = {
            "items": [
                {
                    "sourceProperties": {
                        "hostname": "db-01",
                        "networkInterfaces": [
                            {
                                "vpcId": "vpc-123",
                                "subnetId": "subnet-456",
                                "securityGroupIds": ["sg-aaa", "sg-bbb"],
                            },
                        ],
                        "iamInstanceProfileArn": "arn:aws:iam::111111111111:instance-profile/DBRole",
                    },
                    "stagingArea": {"stagingAccountID": "333333333333"},
                },
            ],
        }

        result = get_recovery_instances_for_region("111111111111", "us-east-1")

        assert result[0]["sourceVpcId"] == "vpc-123"
        assert result[0]["sourceSubnetId"] == "subnet-456"
        assert result[0]["sourceSecurityGroupIds"] == ["sg-aaa", "sg-bbb"]
        assert result[0]["sourceInstanceProfile"] == "arn:aws:iam::111111111111:instance-profile/DBRole"


# ---------------------------------------------------------------------------
# 11.4 Test enrich_with_ec2_details() data transformation
# ---------------------------------------------------------------------------

class TestEnrichWithEc2Details:
    """Tests for enrich_with_ec2_details().

    Validates: Requirements 1.3 (EC2 enrichment)
    """

    @patch("shared.recovery_instance_sync.boto3")
    def test_enrichment_happy_path(self, mock_boto3):
        """Test successful EC2 enrichment with all fields."""
        mock_ec2 = MagicMock()
        mock_boto3.client.return_value = mock_ec2
        mock_ec2.describe_instances.return_value = {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-abc123",
                            "InstanceType": "t3.medium",
                            "PrivateIpAddress": "10.0.1.100",
                            "PublicIpAddress": "54.123.45.67",
                            "LaunchTime": datetime(2025, 1, 1, tzinfo=timezone.utc),
                            "Tags": [{"Key": "Name", "Value": "Recovery of web-01"}],
                        },
                    ],
                },
            ],
        }

        result = enrich_with_ec2_details("i-abc123", "us-east-2", "111111111111")

        assert result["Name"] == "Recovery of web-01"
        assert result["PrivateIpAddress"] == "10.0.1.100"
        assert result["PublicIpAddress"] == "54.123.45.67"
        assert result["InstanceType"] == "t3.medium"
        assert result["LaunchTime"] is not None

    @patch("shared.recovery_instance_sync.boto3")
    def test_enrichment_no_name_tag(self, mock_boto3):
        """Test enrichment when instance has no Name tag."""
        mock_ec2 = MagicMock()
        mock_boto3.client.return_value = mock_ec2
        mock_ec2.describe_instances.return_value = {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-noname",
                            "InstanceType": "t3.small",
                            "PrivateIpAddress": "10.0.0.1",
                            "Tags": [{"Key": "Environment", "Value": "dev"}],
                        },
                    ],
                },
            ],
        }

        result = enrich_with_ec2_details("i-noname", "us-east-2", "111111111111")

        assert result["Name"] == "Recovery instance i-noname"
        assert result["InstanceType"] == "t3.small"

    @patch("shared.recovery_instance_sync.boto3")
    def test_enrichment_no_tags(self, mock_boto3):
        """Test enrichment when instance has no tags at all."""
        mock_ec2 = MagicMock()
        mock_boto3.client.return_value = mock_ec2
        mock_ec2.describe_instances.return_value = {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-notags",
                            "InstanceType": "m5.large",
                            "PrivateIpAddress": "10.0.0.2",
                        },
                    ],
                },
            ],
        }

        result = enrich_with_ec2_details("i-notags", "us-east-2", "111111111111")

        assert result["Name"] == "Recovery instance i-notags"

    @patch("shared.recovery_instance_sync.boto3")
    def test_enrichment_instance_not_found(self, mock_boto3):
        """Test enrichment when EC2 instance is not found."""
        mock_ec2 = MagicMock()
        mock_boto3.client.return_value = mock_ec2
        mock_ec2.describe_instances.return_value = {"Reservations": []}

        result = enrich_with_ec2_details("i-missing", "us-east-2", "111111111111")

        assert result["Name"] == "Recovery instance i-missing"
        assert result["InstanceType"] == "unknown"

    @patch("shared.recovery_instance_sync.boto3")
    def test_enrichment_ec2_client_error_returns_defaults(self, mock_boto3):
        """Test that EC2 ClientError returns default values instead of raising."""
        mock_ec2 = MagicMock()
        mock_boto3.client.return_value = mock_ec2
        mock_ec2.describe_instances.side_effect = _make_client_error(
            "InvalidInstanceID.NotFound", "Instance not found"
        )

        result = enrich_with_ec2_details("i-gone", "us-east-2", "111111111111")

        assert result["Name"] == "Recovery instance i-gone"
        assert result["InstanceType"] == "unknown"

    @patch("shared.recovery_instance_sync.boto3")
    def test_enrichment_unexpected_error_returns_defaults(self, mock_boto3):
        """Test that unexpected errors return default values."""
        mock_ec2 = MagicMock()
        mock_boto3.client.return_value = mock_ec2
        mock_ec2.describe_instances.side_effect = Exception("Network timeout")

        result = enrich_with_ec2_details("i-timeout", "us-east-2", "111111111111")

        assert result["Name"] == "Recovery instance i-timeout"
        assert result["InstanceType"] == "unknown"

    @patch("shared.recovery_instance_sync.boto3")
    def test_enrichment_no_public_ip(self, mock_boto3):
        """Test enrichment when instance has no public IP."""
        mock_ec2 = MagicMock()
        mock_boto3.client.return_value = mock_ec2
        mock_ec2.describe_instances.return_value = {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-private",
                            "InstanceType": "t3.micro",
                            "PrivateIpAddress": "10.0.0.3",
                            "Tags": [{"Key": "Name", "Value": "private-instance"}],
                        },
                    ],
                },
            ],
        }

        result = enrich_with_ec2_details("i-private", "us-east-2", "111111111111")

        assert result["PrivateIpAddress"] == "10.0.0.3"
        assert result.get("PublicIpAddress") is None


# ---------------------------------------------------------------------------
# 11.5 Test find_source_execution() lookup logic
# ---------------------------------------------------------------------------

class TestFindSourceExecution:
    """Tests for find_source_execution().

    Validates: Requirements 1.3 (execution tracking)
    """

    @patch("shared.recovery_instance_sync._get_execution_history_table")
    def test_find_execution_by_server_id(self, mock_get_table):
        """Test finding execution by source server ID."""
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table
        mock_table.scan.return_value = {
            "Items": [
                {
                    "executionId": "exec-001",
                    "planName": "DR Plan A",
                    "startTime": "2025-01-01T10:00:00Z",
                    "sourceServerIds": ["s-abc", "s-def"],
                },
            ],
        }

        result = find_source_execution("s-abc")

        assert result["executionId"] == "exec-001"
        assert result["planName"] == "DR Plan A"

    @patch("shared.recovery_instance_sync._get_execution_history_table")
    def test_find_execution_no_match(self, mock_get_table):
        """Test finding execution when no match exists."""
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table
        mock_table.scan.return_value = {"Items": []}

        result = find_source_execution("s-nonexistent")

        assert result == {}

    @patch("shared.recovery_instance_sync._get_execution_history_table")
    def test_find_execution_with_launch_time_picks_closest(self, mock_get_table):
        """Test that launch_time is used to find the closest execution."""
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table
        mock_table.scan.return_value = {
            "Items": [
                {
                    "executionId": "exec-old",
                    "planName": "Old Plan",
                    "startTime": "2025-01-01T08:00:00Z",
                    "sourceServerIds": ["s-abc"],
                },
                {
                    "executionId": "exec-close",
                    "planName": "Close Plan",
                    "startTime": "2025-01-01T11:55:00Z",
                    "sourceServerIds": ["s-abc"],
                },
            ],
        }

        result = find_source_execution("s-abc", "2025-01-01T12:00:00Z")

        assert result["executionId"] == "exec-close"
        assert result["planName"] == "Close Plan"

    @patch("shared.recovery_instance_sync._get_execution_history_table")
    def test_find_execution_without_launch_time_returns_most_recent(self, mock_get_table):
        """Test that without launch_time, the most recent execution is returned."""
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table
        mock_table.scan.return_value = {
            "Items": [
                {
                    "executionId": "exec-old",
                    "planName": "Old Plan",
                    "startTime": "2025-01-01T08:00:00Z",
                },
                {
                    "executionId": "exec-recent",
                    "planName": "Recent Plan",
                    "startTime": "2025-01-15T10:00:00Z",
                },
            ],
        }

        result = find_source_execution("s-abc")

        assert result["executionId"] == "exec-recent"

    @patch("shared.recovery_instance_sync._get_execution_history_table")
    def test_find_execution_table_error_returns_empty(self, mock_get_table):
        """Test that DynamoDB errors return empty dict instead of raising."""
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table
        mock_table.scan.side_effect = Exception("DynamoDB error")

        result = find_source_execution("s-abc")

        assert result == {}

    @patch("shared.recovery_instance_sync._get_execution_history_table")
    def test_find_execution_invalid_launch_time_falls_back(self, mock_get_table):
        """Test that invalid launch_time falls back to most recent execution."""
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table
        mock_table.scan.return_value = {
            "Items": [
                {
                    "executionId": "exec-fallback",
                    "planName": "Fallback Plan",
                    "startTime": "2025-01-01T10:00:00Z",
                },
            ],
        }

        result = find_source_execution("s-abc", "not-a-valid-date")

        assert result["executionId"] == "exec-fallback"


# ---------------------------------------------------------------------------
# 11.6 Test error handling for API failures
# ---------------------------------------------------------------------------

class TestErrorHandling:
    """Tests for error handling across sync functions.

    Validates: Requirements 8.1-8.7 (error handling and resilience)
    """

    def test_sync_error_is_exception(self):
        """Test RecoveryInstanceSyncError inherits from Exception."""
        error = RecoveryInstanceSyncError("test error")
        assert isinstance(error, Exception)
        assert str(error) == "test error"

    def test_timeout_error_inherits_from_sync_error(self):
        """Test RecoveryInstanceSyncTimeoutError inherits from base error."""
        error = RecoveryInstanceSyncTimeoutError("timeout")
        assert isinstance(error, RecoveryInstanceSyncError)
        assert isinstance(error, Exception)

    def test_validation_error_inherits_from_sync_error(self):
        """Test RecoveryInstanceSyncValidationError inherits from base error."""
        error = RecoveryInstanceSyncValidationError("invalid")
        assert isinstance(error, RecoveryInstanceSyncError)
        assert isinstance(error, Exception)

    def test_missing_recovery_instances_table_env_var(self):
        """Test error when RECOVERY_INSTANCES_CACHE_TABLE is not set."""
        sync_module.RECOVERY_INSTANCES_CACHE_TABLE = None
        sync_module._recovery_instances_table = None

        with pytest.raises(RecoveryInstanceSyncError, match="RECOVERY_INSTANCES_CACHE_TABLE"):
            sync_module._get_recovery_instances_table()

    def test_missing_execution_history_table_env_var(self):
        """Test error when EXECUTION_HISTORY_TABLE is not set."""
        sync_module.EXECUTION_HISTORY_TABLE = None
        sync_module._execution_history_table = None

        with pytest.raises(RecoveryInstanceSyncError, match="EXECUTION_HISTORY_TABLE"):
            sync_module._get_execution_history_table()

    def test_missing_target_accounts_table_env_var(self):
        """Test error when TARGET_ACCOUNTS_TABLE is not set."""
        sync_module.TARGET_ACCOUNTS_TABLE = None
        sync_module._target_accounts_table = None

        with pytest.raises(RecoveryInstanceSyncError, match="TARGET_ACCOUNTS_TABLE"):
            sync_module._get_target_accounts_table()

    @patch("shared.recovery_instance_sync._get_recovery_instances_table")
    def test_get_sync_status_table_error_returns_error_status(self, mock_get_table):
        """Test that sync status returns error status on DynamoDB failure."""
        mock_get_table.side_effect = Exception("Table not found")

        result = get_recovery_instance_sync_status()

        assert result["status"] == "error"
        assert result["lastSyncTime"] is None
        assert len(result["errors"]) == 1

    @patch("shared.recovery_instance_sync._get_target_accounts_table")
    def test_get_target_accounts_failure_raises(self, mock_get_table):
        """Test that target accounts query failure raises RecoveryInstanceSyncError."""
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table
        mock_table.scan.side_effect = Exception("DynamoDB unavailable")

        with pytest.raises(RecoveryInstanceSyncError, match="Failed to get target accounts"):
            sync_module._get_target_accounts()

    @patch("shared.recovery_instance_sync.boto3")
    def test_drs_unexpected_error_raises_sync_error(self, mock_boto3):
        """Test that unexpected DRS errors are wrapped in RecoveryInstanceSyncError."""
        mock_drs = MagicMock()
        mock_boto3.client.return_value = mock_drs
        mock_drs.describe_recovery_instances.side_effect = RuntimeError("Unexpected")

        with pytest.raises(RecoveryInstanceSyncError, match="Unexpected error"):
            get_recovery_instances_for_region("111111111111", "us-east-1")

    @patch("shared.recovery_instance_sync.boto3")
    def test_ec2_client_creation_failure_returns_defaults(self, mock_boto3):
        """Test that EC2 client creation failure returns default values."""
        mock_boto3.client.side_effect = Exception("Cannot create client")

        result = enrich_with_ec2_details(
            "i-abc", "us-east-2", "111111111111",
            account_context={"isCurrentAccount": False, "accountId": "222222222222", "assumeRoleName": "role"}
        )

        assert result["InstanceType"] == "unknown"


# ---------------------------------------------------------------------------
# 11.7 Test cross-account role assumption
# ---------------------------------------------------------------------------

class TestCrossAccountRoleAssumption:
    """Tests for cross-account DRS and EC2 client creation.

    Validates: Requirements 9.1-9.6 (cross-account support)
    """

    @patch("shared.recovery_instance_sync.boto3")
    def test_current_account_uses_default_drs_client(self, mock_boto3):
        """Test that current account uses default boto3 DRS client."""
        mock_drs = MagicMock()
        mock_boto3.client.return_value = mock_drs
        mock_drs.describe_recovery_instances.return_value = {"items": []}

        get_recovery_instances_for_region("111111111111", "us-east-1", account_context=None)

        mock_boto3.client.assert_called_with("drs", region_name="us-east-1")

    @patch("shared.recovery_instance_sync.boto3")
    def test_current_account_flag_uses_default_client(self, mock_boto3):
        """Test that isCurrentAccount=True uses default boto3 client."""
        mock_drs = MagicMock()
        mock_boto3.client.return_value = mock_drs
        mock_drs.describe_recovery_instances.return_value = {"items": []}

        context = {"accountId": "111111111111", "isCurrentAccount": True}
        get_recovery_instances_for_region("111111111111", "us-east-1", account_context=context)

        mock_boto3.client.assert_called_with("drs", region_name="us-east-1")

    @patch("shared.cross_account.get_cross_account_session")
    def test_cross_account_drs_client_assumes_role(self, mock_get_session):
        """Test that cross-account context triggers role assumption for DRS."""
        mock_session = MagicMock()
        mock_drs = MagicMock()
        mock_session.client.return_value = mock_drs
        mock_get_session.return_value = mock_session

        account_context = {
            "accountId": "222222222222",
            "assumeRoleName": "DRSCrossAccountRole",
            "externalId": "ext-abc",
            "isCurrentAccount": False,
        }

        result = sync_module._get_cross_account_drs_client("us-east-1", account_context)

        mock_get_session.assert_called_once_with(
            "arn:aws:iam::222222222222:role/DRSCrossAccountRole", "ext-abc"
        )
        mock_session.client.assert_called_once_with("drs", region_name="us-east-1")
        assert result == mock_drs

    @patch("shared.cross_account.get_cross_account_session")
    def test_cross_account_ec2_client_assumes_role(self, mock_get_session):
        """Test that cross-account context triggers role assumption for EC2."""
        mock_session = MagicMock()
        mock_ec2 = MagicMock()
        mock_session.client.return_value = mock_ec2
        mock_get_session.return_value = mock_session

        account_context = {
            "accountId": "333333333333",
            "assumeRoleName": "EC2CrossAccountRole",
            "externalId": "ext-xyz",
            "isCurrentAccount": False,
        }

        result = sync_module._get_cross_account_ec2_client("us-west-2", account_context)

        mock_get_session.assert_called_once_with(
            "arn:aws:iam::333333333333:role/EC2CrossAccountRole", "ext-xyz"
        )
        mock_session.client.assert_called_once_with("ec2", region_name="us-west-2")
        assert result == mock_ec2

    @patch("shared.recovery_instance_sync.boto3")
    def test_cross_account_no_role_uses_default_drs_client(self, mock_boto3):
        """Test that cross-account without assumeRoleName uses default client."""
        mock_drs = MagicMock()
        mock_boto3.client.return_value = mock_drs

        account_context = {"accountId": "111111111111"}

        result = sync_module._get_cross_account_drs_client("us-east-1", account_context)

        mock_boto3.client.assert_called_with("drs", region_name="us-east-1")
        assert result == mock_drs

    @patch("shared.recovery_instance_sync.boto3")
    def test_cross_account_no_role_uses_default_ec2_client(self, mock_boto3):
        """Test that cross-account without assumeRoleName uses default EC2 client."""
        mock_ec2 = MagicMock()
        mock_boto3.client.return_value = mock_ec2

        account_context = {"accountId": "111111111111"}

        result = sync_module._get_cross_account_ec2_client("us-east-1", account_context)

        mock_boto3.client.assert_called_with("ec2", region_name="us-east-1")
        assert result == mock_ec2

    @patch("shared.cross_account.get_cross_account_session")
    def test_cross_account_role_assumption_failure_raises(self, mock_get_session):
        """Test that role assumption failure raises RecoveryInstanceSyncError."""
        mock_get_session.side_effect = Exception("Access denied")

        account_context = {
            "accountId": "999999999999",
            "assumeRoleName": "BadRole",
            "isCurrentAccount": False,
        }

        with pytest.raises(RecoveryInstanceSyncError, match="Failed to create cross-account DRS client"):
            sync_module._get_cross_account_drs_client("us-east-1", account_context)

    @patch("shared.cross_account.get_cross_account_session")
    def test_cross_account_ec2_role_assumption_failure_raises(self, mock_get_session):
        """Test that EC2 role assumption failure raises RecoveryInstanceSyncError."""
        mock_get_session.side_effect = Exception("STS error")

        account_context = {
            "accountId": "999999999999",
            "assumeRoleName": "BadRole",
            "isCurrentAccount": False,
        }

        with pytest.raises(RecoveryInstanceSyncError, match="Failed to create cross-account EC2 client"):
            sync_module._get_cross_account_ec2_client("us-east-1", account_context)


# ---------------------------------------------------------------------------
# Additional: Test get_recovery_instance_sync_status()
# ---------------------------------------------------------------------------

class TestGetRecoveryInstanceSyncStatus:
    """Tests for get_recovery_instance_sync_status().

    Validates: Requirements 2.2 (status retrieval)
    """

    @patch("shared.recovery_instance_sync._get_recovery_instances_table")
    def test_status_with_existing_data(self, mock_get_table):
        """Test status when cache has data."""
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table
        mock_table.scan.side_effect = [
            {"Items": [{"lastSyncTime": "2025-02-17T10:35:00Z"}]},
            {"Count": 42},
        ]

        result = get_recovery_instance_sync_status()

        assert result["lastSyncTime"] == "2025-02-17T10:35:00Z"
        assert result["instancesUpdated"] == 42
        assert result["status"] == "healthy"
        assert result["errors"] == []

    @patch("shared.recovery_instance_sync._get_recovery_instances_table")
    def test_status_with_empty_cache(self, mock_get_table):
        """Test status when cache is empty."""
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table
        mock_table.scan.return_value = {"Items": []}

        result = get_recovery_instance_sync_status()

        assert result["lastSyncTime"] is None
        assert result["instancesUpdated"] == 0
        assert result["status"] == "no_sync_yet"

    @patch("shared.recovery_instance_sync._get_recovery_instances_table")
    def test_status_on_error(self, mock_get_table):
        """Test status when DynamoDB query fails."""
        mock_get_table.side_effect = Exception("Connection refused")

        result = get_recovery_instance_sync_status()

        assert result["status"] == "error"
        assert result["lastSyncTime"] is None
        assert len(result["errors"]) == 1
        assert "Connection refused" in result["errors"][0]


# ---------------------------------------------------------------------------
# Additional: Test _get_target_accounts()
# ---------------------------------------------------------------------------

class TestGetTargetAccounts:
    """Tests for _get_target_accounts() helper.

    Validates: Requirements 9.1 (cross-account discovery)
    """

    @patch("shared.recovery_instance_sync._get_target_accounts_table")
    def test_returns_accounts_with_regions(self, mock_get_table):
        """Test that target accounts are returned with regions."""
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table
        mock_table.scan.return_value = {
            "Items": [
                {"accountId": "111111111111", "regions": ["us-east-1", "us-west-2"]},
                {"accountId": "222222222222", "regions": ["eu-west-1"]},
            ],
        }

        result = sync_module._get_target_accounts()

        assert len(result) == 2
        assert result[0]["accountId"] == "111111111111"
        assert result[0]["regions"] == ["us-east-1", "us-west-2"]
        assert result[1]["accountId"] == "222222222222"

    @patch("shared.recovery_instance_sync._get_target_accounts_table")
    def test_returns_empty_list_when_no_accounts(self, mock_get_table):
        """Test that empty list is returned when no accounts exist."""
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table
        mock_table.scan.return_value = {"Items": []}

        result = sync_module._get_target_accounts()

        assert result == []

    @patch("shared.recovery_instance_sync._get_target_accounts_table")
    def test_includes_account_context(self, mock_get_table):
        """Test that full account item is included as accountContext."""
        mock_table = MagicMock()
        mock_get_table.return_value = mock_table
        item = {"accountId": "111111111111", "regions": ["us-east-1"], "assumeRoleName": "CrossRole"}
        mock_table.scan.return_value = {"Items": [item]}

        result = sync_module._get_target_accounts()

        assert result[0]["accountContext"] == item
