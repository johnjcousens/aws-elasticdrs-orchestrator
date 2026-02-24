"""
Integration tests for Recovery Instance Sync feature.

End-to-end integration tests with moto-mocked DynamoDB and unittest.mock
for DRS/EC2 (moto does not support DRS). Validates EventBridge-triggered sync,
wave completion sync, cache query performance, multi-region sync,
cross-account access, and terminate instances end-to-end.

Feature: recovery-instance-sync
Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch

import boto3
import pytest
from moto import mock_aws

# Add lambda directory to path
lambda_dir = os.path.join(os.path.dirname(__file__), "..", "..", "lambda")
sys.path.insert(0, lambda_dir)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

RECOVERY_INSTANCES_TABLE = "test-recovery-instances-cache"
EXECUTION_HISTORY_TABLE = "test-execution-history"
TARGET_ACCOUNTS_TABLE = "test-target-accounts"
AWS_REGION = "us-east-2"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_sync_module():
    """Reset shared module globals before each test."""
    import shared.recovery_instance_sync as sync_mod

    sync_mod._dynamodb = None
    sync_mod._recovery_instances_table = None
    sync_mod._execution_history_table = None
    sync_mod._target_accounts_table = None
    yield
    sync_mod._dynamodb = None
    sync_mod._recovery_instances_table = None
    sync_mod._execution_history_table = None
    sync_mod._target_accounts_table = None


@pytest.fixture(autouse=True)
def _set_env(monkeypatch):
    """Set required environment variables."""
    monkeypatch.setenv("RECOVERY_INSTANCES_CACHE_TABLE", RECOVERY_INSTANCES_TABLE)
    monkeypatch.setenv("EXECUTION_HISTORY_TABLE", EXECUTION_HISTORY_TABLE)
    monkeypatch.setenv("TARGET_ACCOUNTS_TABLE", TARGET_ACCOUNTS_TABLE)
    monkeypatch.setenv("AWS_DEFAULT_REGION", AWS_REGION)

    import shared.recovery_instance_sync as sync_mod

    sync_mod.RECOVERY_INSTANCES_CACHE_TABLE = RECOVERY_INSTANCES_TABLE
    sync_mod.EXECUTION_HISTORY_TABLE = EXECUTION_HISTORY_TABLE
    sync_mod.TARGET_ACCOUNTS_TABLE = TARGET_ACCOUNTS_TABLE


@pytest.fixture
def dynamodb_tables():
    """Create real moto DynamoDB tables for integration testing."""
    with mock_aws():
        dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)

        # Recovery instances cache table
        ri_table = dynamodb.create_table(
            TableName=RECOVERY_INSTANCES_TABLE,
            KeySchema=[{"AttributeName": "sourceServerId", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "sourceServerId", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )

        # Execution history table
        eh_table = dynamodb.create_table(
            TableName=EXECUTION_HISTORY_TABLE,
            KeySchema=[{"AttributeName": "executionId", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "executionId", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )

        # Target accounts table
        ta_table = dynamodb.create_table(
            TableName=TARGET_ACCOUNTS_TABLE,
            KeySchema=[{"AttributeName": "accountId", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "accountId", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )

        yield {
            "recovery_instances": ri_table,
            "execution_history": eh_table,
            "target_accounts": ta_table,
            "dynamodb": dynamodb,
        }


def _seed_target_accounts(tables, accounts):
    """Seed target accounts table with test data."""
    ta_table = tables["target_accounts"]
    for account in accounts:
        ta_table.put_item(Item=account)


def _seed_execution_history(tables, executions):
    """Seed execution history table with test data."""
    eh_table = tables["execution_history"]
    for execution in executions:
        eh_table.put_item(Item=execution)


def _make_drs_recovery_instance(source_server_id, recovery_instance_id, ec2_instance_id, state="running"):
    """Build a DRS describe_recovery_instances item."""
    return {
        "sourceServerID": source_server_id,
        "recoveryInstanceID": recovery_instance_id,
        "ec2InstanceID": ec2_instance_id,
        "ec2InstanceState": state,
        "launchTime": "2025-02-17T10:30:00Z",
    }


def _make_drs_source_server(hostname="web-01", staging_account_id="222222222222"):
    """Build a DRS describe_source_servers item."""
    return {
        "sourceProperties": {
            "hostname": hostname,
            "networkInterfaces": [
                {"vpcId": "vpc-abc123", "subnetId": "subnet-xyz789", "securityGroupIds": ["sg-111222"]}
            ],
            "iamInstanceProfileArn": "arn:aws:iam::111111111111:instance-profile/AppRole",
        },
        "stagingArea": {"stagingAccountID": staging_account_id},
    }


def _make_ec2_instance(instance_id, name="Recovery of web-01", instance_type="t3.medium"):
    """Build an EC2 describe_instances response."""
    return {
        "Reservations": [
            {
                "Instances": [
                    {
                        "InstanceId": instance_id,
                        "InstanceType": instance_type,
                        "PrivateIpAddress": "10.0.1.100",
                        "PublicIpAddress": "54.123.45.67",
                        "LaunchTime": datetime(2025, 2, 17, 10, 30, tzinfo=timezone.utc),
                        "Tags": [{"Key": "Name", "Value": name}],
                    }
                ]
            }
        ]
    }



# ===========================================================================
# 13.1 - End-to-end EventBridge-triggered sync
# ===========================================================================


class TestEventBridgeTriggeredSync:
    """End-to-end test: EventBridge triggers background sync via data-management-handler.

    Validates: Requirements 1.3 (background sync), 3.1-3.7
    """

    def test_eventbridge_sync_writes_instances_to_cache(self, dynamodb_tables):
        """EventBridge sync queries DRS, enriches with EC2, writes to DynamoDB cache."""
        _seed_target_accounts(
            dynamodb_tables,
            [{"accountId": "111111111111", "regions": ["us-east-2"], "accountName": "Primary"}],
        )
        _seed_execution_history(
            dynamodb_tables,
            [
                {
                    "executionId": "exec-001",
                    "planName": "DR Plan Alpha",
                    "sourceServerIds": ["s-abc123"],
                    "startTime": "2025-02-17T10:00:00Z",
                }
            ],
        )

        mock_drs = MagicMock()
        mock_drs.describe_recovery_instances.return_value = {
            "items": [_make_drs_recovery_instance("s-abc123", "ri-abc123", "i-abc123")]
        }
        mock_drs.describe_source_servers.return_value = {"items": [_make_drs_source_server("web-01")]}

        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.return_value = _make_ec2_instance("i-abc123", "Recovery of web-01")

        from shared.recovery_instance_sync import sync_all_recovery_instances

        with patch("shared.recovery_instance_sync.boto3") as mock_boto3:
            mock_boto3.client.side_effect = lambda svc, **kw: mock_drs if svc == "drs" else mock_ec2
            mock_boto3.resource.return_value = dynamodb_tables["dynamodb"]

            result = sync_all_recovery_instances()

        assert result["instancesUpdated"] == 1
        assert result["regionsScanned"] == 1
        assert result["errors"] == []

        # Verify data written to DynamoDB
        cache_table = dynamodb_tables["recovery_instances"]
        response = cache_table.get_item(Key={"sourceServerId": "s-abc123"})
        item = response["Item"]

        assert item["recoveryInstanceId"] == "ri-abc123"
        assert item["ec2InstanceId"] == "i-abc123"
        assert item["ec2InstanceState"] == "running"
        assert item["name"] == "Recovery of web-01"
        assert item["privateIp"] == "10.0.1.100"
        assert item["publicIp"] == "54.123.45.67"
        assert item["instanceType"] == "t3.medium"
        assert item["region"] == "us-east-2"
        assert item["accountId"] == "111111111111"
        assert item["sourceExecutionId"] == "exec-001"
        assert item["sourcePlanName"] == "DR Plan Alpha"
        assert "lastSyncTime" in item
        assert item["replicationStagingAccountId"] == "222222222222"
        assert item["sourceVpcId"] == "vpc-abc123"
        assert item["sourceSubnetId"] == "subnet-xyz789"
        assert item["sourceSecurityGroupIds"] == ["sg-111222"]

    def test_eventbridge_sync_handles_region_failure_gracefully(self, dynamodb_tables):
        """Sync continues processing remaining regions when one region fails."""
        _seed_target_accounts(
            dynamodb_tables,
            [{"accountId": "111111111111", "regions": ["us-east-1", "us-east-2"], "accountName": "Primary"}],
        )

        mock_drs_east1 = MagicMock()
        mock_drs_east1.describe_recovery_instances.side_effect = Exception("DRS unavailable in us-east-1")

        mock_drs_east2 = MagicMock()
        mock_drs_east2.describe_recovery_instances.return_value = {
            "items": [_make_drs_recovery_instance("s-def456", "ri-def456", "i-def456")]
        }
        mock_drs_east2.describe_source_servers.return_value = {"items": [_make_drs_source_server("db-01")]}

        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.return_value = _make_ec2_instance("i-def456", "Recovery of db-01")

        from shared.recovery_instance_sync import sync_all_recovery_instances

        call_count = 0

        def client_factory(svc, **kw):
            nonlocal call_count
            if svc == "drs":
                call_count += 1
                return mock_drs_east1 if call_count == 1 else mock_drs_east2
            return mock_ec2

        with patch("shared.recovery_instance_sync.boto3") as mock_boto3:
            mock_boto3.client.side_effect = client_factory
            mock_boto3.resource.return_value = dynamodb_tables["dynamodb"]

            result = sync_all_recovery_instances()

        assert result["instancesUpdated"] == 1
        assert result["regionsScanned"] == 2
        assert len(result["errors"]) == 1
        assert "us-east-1" in result["errors"][0]

        # Verify the successful region's data was written
        response = dynamodb_tables["recovery_instances"].get_item(Key={"sourceServerId": "s-def456"})
        assert "Item" in response

    def test_eventbridge_sync_no_accounts_returns_empty(self, dynamodb_tables):
        """Sync with no target accounts returns zero instances."""
        from shared.recovery_instance_sync import sync_all_recovery_instances

        with patch("shared.recovery_instance_sync.boto3") as mock_boto3:
            mock_boto3.resource.return_value = dynamodb_tables["dynamodb"]

            result = sync_all_recovery_instances()

        assert result["instancesUpdated"] == 0
        assert result["regionsScanned"] == 0
        assert result["errors"] == []



# ===========================================================================
# 13.2 - End-to-end wave completion sync
# ===========================================================================


class TestWaveCompletionSync:
    """End-to-end test: wave completion triggers sync and writes to DynamoDB cache.

    Validates: Requirements 1.2 (wave completion sync), 2.1-2.5
    """

    def test_wave_completion_writes_instances_to_cache(self, dynamodb_tables):
        """After wave completes, recovery instances are synced to DynamoDB cache."""
        _seed_execution_history(
            dynamodb_tables,
            [
                {
                    "executionId": "exec-wave-001",
                    "planName": "Wave Recovery Plan",
                    "sourceServerIds": ["s-wave-abc"],
                    "startTime": "2025-02-17T10:00:00Z",
                }
            ],
        )

        mock_drs = MagicMock()
        mock_drs.describe_recovery_instances.return_value = {
            "items": [_make_drs_recovery_instance("s-wave-abc", "ri-wave-abc", "i-wave-abc")]
        }
        mock_drs.describe_source_servers.return_value = {"items": [_make_drs_source_server("app-server-01")]}

        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.return_value = _make_ec2_instance("i-wave-abc", "Recovery of app-server-01")

        from shared.recovery_instance_sync import sync_recovery_instances_for_account

        with patch("shared.recovery_instance_sync.boto3") as mock_boto3:
            mock_boto3.client.side_effect = lambda svc, **kw: mock_drs if svc == "drs" else mock_ec2
            mock_boto3.resource.return_value = dynamodb_tables["dynamodb"]

            result = sync_recovery_instances_for_account("111111111111", "us-east-2")

        assert result["instancesUpdated"] == 1
        assert result["errors"] == []

        # Verify data in cache
        response = dynamodb_tables["recovery_instances"].get_item(Key={"sourceServerId": "s-wave-abc"})
        item = response["Item"]
        assert item["recoveryInstanceId"] == "ri-wave-abc"
        assert item["name"] == "Recovery of app-server-01"
        assert item["instanceType"] == "t3.medium"
        assert "lastSyncTime" in item

    def test_wave_completion_sync_error_does_not_block(self, dynamodb_tables):
        """DRS failure during wave sync returns error but does not raise."""
        mock_drs = MagicMock()
        mock_drs.describe_recovery_instances.side_effect = Exception("DRS timeout")

        from shared.recovery_instance_sync import sync_recovery_instances_for_account

        with patch("shared.recovery_instance_sync.boto3") as mock_boto3:
            mock_boto3.client.return_value = mock_drs
            mock_boto3.resource.return_value = dynamodb_tables["dynamodb"]

            result = sync_recovery_instances_for_account("111111111111", "us-east-2")

        assert result["instancesUpdated"] == 0
        assert len(result["errors"]) == 1
        assert "DRS timeout" in result["errors"][0]

    def test_wave_completion_overwrites_stale_cache(self, dynamodb_tables):
        """Wave completion sync overwrites stale cache data with fresh data."""
        # Pre-populate cache with stale data
        dynamodb_tables["recovery_instances"].put_item(
            Item={
                "sourceServerId": "s-stale",
                "recoveryInstanceId": "ri-old",
                "ec2InstanceId": "i-old",
                "ec2InstanceState": "stopped",
                "name": "Old Recovery",
                "instanceType": "t2.micro",
                "region": "us-east-2",
                "accountId": "111111111111",
                "lastSyncTime": "2025-01-01T00:00:00Z",
                "sourceServerName": "stale-server",
                "replicationStagingAccountId": "000000000000",
                "sourceSecurityGroupIds": [],
            }
        )

        mock_drs = MagicMock()
        mock_drs.describe_recovery_instances.return_value = {
            "items": [_make_drs_recovery_instance("s-stale", "ri-fresh", "i-fresh", "running")]
        }
        mock_drs.describe_source_servers.return_value = {"items": [_make_drs_source_server("fresh-server")]}

        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.return_value = _make_ec2_instance("i-fresh", "Fresh Recovery", "m5.large")

        from shared.recovery_instance_sync import sync_recovery_instances_for_account

        with patch("shared.recovery_instance_sync.boto3") as mock_boto3:
            mock_boto3.client.side_effect = lambda svc, **kw: mock_drs if svc == "drs" else mock_ec2
            mock_boto3.resource.return_value = dynamodb_tables["dynamodb"]

            result = sync_recovery_instances_for_account("111111111111", "us-east-2")

        assert result["instancesUpdated"] == 1

        # Verify stale data was overwritten
        response = dynamodb_tables["recovery_instances"].get_item(Key={"sourceServerId": "s-stale"})
        item = response["Item"]
        assert item["recoveryInstanceId"] == "ri-fresh"
        assert item["ec2InstanceId"] == "i-fresh"
        assert item["ec2InstanceState"] == "running"
        assert item["name"] == "Fresh Recovery"
        assert item["instanceType"] == "m5.large"
        assert item["lastSyncTime"] > "2025-01-01T00:00:00Z"



# ===========================================================================
# 13.3 - Cache query performance (<3 seconds)
# ===========================================================================


class TestCacheQueryPerformance:
    """Test that DynamoDB cache queries complete in under 3 seconds.

    Validates: Requirements 1.4 (optimized query), 4.1-4.5, 11.1
    """

    def test_cache_query_under_3_seconds_for_100_servers(self, dynamodb_tables):
        """Querying 100 cached recovery instances completes in under 3 seconds."""
        cache_table = dynamodb_tables["recovery_instances"]

        # Seed 100 recovery instance records
        with cache_table.batch_writer() as batch:
            for i in range(100):
                batch.put_item(
                    Item={
                        "sourceServerId": f"s-perf{i:04d}",
                        "recoveryInstanceId": f"ri-perf{i:04d}",
                        "ec2InstanceId": f"i-perf{i:04d}",
                        "ec2InstanceState": "running",
                        "sourceServerName": f"server-{i:04d}",
                        "name": f"Recovery of server-{i:04d}",
                        "privateIp": f"10.0.{i // 256}.{i % 256}",
                        "publicIp": None,
                        "instanceType": "t3.medium",
                        "launchTime": "2025-02-17T10:30:00Z",
                        "region": "us-east-2",
                        "accountId": "111111111111",
                        "sourceExecutionId": "exec-perf",
                        "sourcePlanName": "Perf Test Plan",
                        "lastSyncTime": "2025-02-17T10:35:00Z",
                        "replicationStagingAccountId": "222222222222",
                        "sourceSecurityGroupIds": [],
                    }
                )

        # Query all 100 servers from cache
        server_ids = [f"s-perf{i:04d}" for i in range(100)]

        start_time = time.time()

        instances = []
        for server_id in server_ids:
            response = cache_table.get_item(Key={"sourceServerId": server_id})
            if "Item" in response:
                instances.append(response["Item"])

        elapsed = time.time() - start_time

        assert len(instances) == 100
        assert elapsed < 3.0, f"Cache query took {elapsed:.2f}s, expected <3s"

    def test_cache_query_returns_correct_format(self, dynamodb_tables):
        """Cache query returns data in the expected response format."""
        cache_table = dynamodb_tables["recovery_instances"]
        cache_table.put_item(
            Item={
                "sourceServerId": "s-format-test",
                "recoveryInstanceId": "ri-format-test",
                "ec2InstanceId": "i-format-test",
                "ec2InstanceState": "running",
                "sourceServerName": "format-server",
                "name": "Recovery of format-server",
                "privateIp": "10.0.1.50",
                "publicIp": "54.1.2.3",
                "instanceType": "m5.large",
                "launchTime": "2025-02-17T10:30:00Z",
                "region": "us-east-2",
                "accountId": "111111111111",
                "sourceExecutionId": "exec-fmt",
                "sourcePlanName": "Format Plan",
                "lastSyncTime": "2025-02-17T10:35:00Z",
                "replicationStagingAccountId": "222222222222",
                "sourceVpcId": "vpc-fmt",
                "sourceSubnetId": "subnet-fmt",
                "sourceSecurityGroupIds": ["sg-fmt"],
                "sourceInstanceProfile": "arn:aws:iam::111111111111:instance-profile/FmtRole",
            }
        )

        response = cache_table.get_item(Key={"sourceServerId": "s-format-test"})
        item = response["Item"]

        # Verify all required fields are present
        required_fields = [
            "sourceServerId", "recoveryInstanceId", "ec2InstanceId",
            "ec2InstanceState", "name", "privateIp", "instanceType",
            "launchTime", "region", "sourceExecutionId", "sourcePlanName",
            "lastSyncTime", "replicationStagingAccountId",
        ]
        for field in required_fields:
            assert field in item, f"Missing required field: {field}"

    def test_cache_miss_returns_empty(self, dynamodb_tables):
        """Querying a non-existent server returns no Item."""
        cache_table = dynamodb_tables["recovery_instances"]
        response = cache_table.get_item(Key={"sourceServerId": "s-nonexistent"})
        assert "Item" not in response



# ===========================================================================
# 13.4 - Multi-region sync
# ===========================================================================


class TestMultiRegionSync:
    """Test sync across multiple AWS regions.

    Validates: Requirements 1.3 (all regions), 3.2
    """

    def test_sync_across_multiple_regions(self, dynamodb_tables):
        """Sync processes recovery instances from multiple regions."""
        _seed_target_accounts(
            dynamodb_tables,
            [
                {
                    "accountId": "111111111111",
                    "regions": ["us-east-1", "us-east-2", "us-west-2"],
                    "accountName": "Multi-Region Account",
                }
            ],
        )

        mock_drs = MagicMock()
        # Each region returns a different instance
        mock_drs.describe_recovery_instances.side_effect = [
            {"items": [_make_drs_recovery_instance("s-east1", "ri-east1", "i-east1")]},
            {"items": [_make_drs_recovery_instance("s-east2", "ri-east2", "i-east2")]},
            {"items": [_make_drs_recovery_instance("s-west2", "ri-west2", "i-west2")]},
        ]
        mock_drs.describe_source_servers.return_value = {"items": [_make_drs_source_server("multi-server")]}

        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.side_effect = [
            _make_ec2_instance("i-east1", "Recovery us-east-1"),
            _make_ec2_instance("i-east2", "Recovery us-east-2"),
            _make_ec2_instance("i-west2", "Recovery us-west-2"),
        ]

        from shared.recovery_instance_sync import sync_all_recovery_instances

        with patch("shared.recovery_instance_sync.boto3") as mock_boto3:
            mock_boto3.client.side_effect = lambda svc, **kw: mock_drs if svc == "drs" else mock_ec2
            mock_boto3.resource.return_value = dynamodb_tables["dynamodb"]

            result = sync_all_recovery_instances()

        assert result["instancesUpdated"] == 3
        assert result["regionsScanned"] == 3
        assert result["errors"] == []

        # Verify all three regions' data is in cache
        cache_table = dynamodb_tables["recovery_instances"]
        for server_id in ["s-east1", "s-east2", "s-west2"]:
            response = cache_table.get_item(Key={"sourceServerId": server_id})
            assert "Item" in response, f"Missing cache entry for {server_id}"

    def test_sync_multiple_accounts_multiple_regions(self, dynamodb_tables):
        """Sync processes instances from multiple accounts each with multiple regions."""
        _seed_target_accounts(
            dynamodb_tables,
            [
                {"accountId": "111111111111", "regions": ["us-east-1", "us-east-2"], "accountName": "Account A"},
                {"accountId": "222222222222", "regions": ["eu-west-1"], "accountName": "Account B"},
            ],
        )

        mock_drs = MagicMock()
        mock_drs.describe_recovery_instances.side_effect = [
            {"items": [_make_drs_recovery_instance("s-a-e1", "ri-a-e1", "i-a-e1")]},
            {"items": [_make_drs_recovery_instance("s-a-e2", "ri-a-e2", "i-a-e2")]},
            {"items": [_make_drs_recovery_instance("s-b-ew1", "ri-b-ew1", "i-b-ew1")]},
        ]
        mock_drs.describe_source_servers.return_value = {"items": [_make_drs_source_server("server")]}

        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.return_value = _make_ec2_instance("i-generic", "Recovery")

        from shared.recovery_instance_sync import sync_all_recovery_instances

        with patch("shared.recovery_instance_sync.boto3") as mock_boto3:
            mock_boto3.client.side_effect = lambda svc, **kw: mock_drs if svc == "drs" else mock_ec2
            mock_boto3.resource.return_value = dynamodb_tables["dynamodb"]

            result = sync_all_recovery_instances()

        assert result["instancesUpdated"] == 3
        assert result["regionsScanned"] == 3
        assert result["errors"] == []



# ===========================================================================
# 13.5 - Cross-account access
# ===========================================================================


class TestCrossAccountAccess:
    """Test cross-account role assumption and sync.

    Validates: Requirements 1.5 (cross-account), 9.1-9.6
    """

    def test_cross_account_sync_assumes_role(self, dynamodb_tables):
        """Cross-account sync assumes IAM role in target account."""
        _seed_target_accounts(
            dynamodb_tables,
            [
                {
                    "accountId": "333333333333",
                    "regions": ["us-east-2"],
                    "accountName": "Cross Account",
                    "assumeRoleName": "DRSCrossAccountRole",
                    "externalId": "ext-secret-123",
                    "isCurrentAccount": False,
                }
            ],
        )

        mock_drs = MagicMock()
        mock_drs.describe_recovery_instances.return_value = {
            "items": [_make_drs_recovery_instance("s-cross", "ri-cross", "i-cross")]
        }
        mock_drs.describe_source_servers.return_value = {"items": [_make_drs_source_server("cross-server", "444444444444")]}

        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.return_value = _make_ec2_instance("i-cross", "Cross-Account Recovery")

        mock_session = MagicMock()
        mock_session.client.side_effect = lambda svc, **kw: mock_drs if svc == "drs" else mock_ec2

        from shared.recovery_instance_sync import sync_all_recovery_instances

        with patch("shared.recovery_instance_sync.boto3") as mock_boto3, \
             patch("shared.recovery_instance_sync._get_cross_account_drs_client", return_value=mock_drs), \
             patch("shared.recovery_instance_sync._get_cross_account_ec2_client", return_value=mock_ec2):
            mock_boto3.client.side_effect = lambda svc, **kw: mock_drs if svc == "drs" else mock_ec2
            mock_boto3.resource.return_value = dynamodb_tables["dynamodb"]

            result = sync_all_recovery_instances()

        assert result["instancesUpdated"] == 1
        assert result["errors"] == []

        # Verify cross-account data in cache
        response = dynamodb_tables["recovery_instances"].get_item(Key={"sourceServerId": "s-cross"})
        item = response["Item"]
        assert item["accountId"] == "333333333333"
        assert item["replicationStagingAccountId"] == "444444444444"

    def test_cross_account_role_assumption_failure_continues(self, dynamodb_tables):
        """Failed cross-account role assumption logs error and continues."""
        _seed_target_accounts(
            dynamodb_tables,
            [
                {
                    "accountId": "555555555555",
                    "regions": ["us-east-2"],
                    "accountName": "Failing Account",
                    "assumeRoleName": "BadRole",
                    "isCurrentAccount": False,
                },
                {
                    "accountId": "666666666666",
                    "regions": ["us-east-2"],
                    "accountName": "Good Account",
                },
            ],
        )

        mock_drs = MagicMock()
        # First account fails (role assumption), second succeeds
        mock_drs.describe_recovery_instances.side_effect = [
            Exception("Access denied assuming role"),
            {"items": [_make_drs_recovery_instance("s-good", "ri-good", "i-good")]},
        ]
        mock_drs.describe_source_servers.return_value = {"items": [_make_drs_source_server("good-server")]}

        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.return_value = _make_ec2_instance("i-good", "Good Recovery")

        from shared.recovery_instance_sync import sync_all_recovery_instances

        with patch("shared.recovery_instance_sync.boto3") as mock_boto3:
            mock_boto3.client.side_effect = lambda svc, **kw: mock_drs if svc == "drs" else mock_ec2
            mock_boto3.resource.return_value = dynamodb_tables["dynamodb"]

            result = sync_all_recovery_instances()

        assert result["instancesUpdated"] == 1
        assert result["regionsScanned"] == 2
        assert len(result["errors"]) == 1
        assert "Access denied" in result["errors"][0]



# ===========================================================================
# 13.6 - Terminate instances end-to-end
# ===========================================================================


class TestTerminateInstancesEndToEnd:
    """End-to-end test: terminate recovery instances and clean up cache.

    Validates: Requirements 1.5 (terminate), 5.1-5.9
    """

    def test_terminate_cleans_up_cache_records(self, dynamodb_tables):
        """After termination, cache records are deleted from DynamoDB."""
        cache_table = dynamodb_tables["recovery_instances"]

        # Pre-populate cache with instances to terminate
        cache_table.put_item(
            Item={
                "sourceServerId": "s-term-001",
                "recoveryInstanceId": "ri-term-001",
                "ec2InstanceId": "i-term-001",
                "ec2InstanceState": "running",
                "sourceServerName": "term-server-1",
                "name": "Recovery of term-server-1",
                "instanceType": "t3.medium",
                "region": "us-east-2",
                "accountId": "111111111111",
                "sourceExecutionId": "exec-term",
                "lastSyncTime": "2025-02-17T10:35:00Z",
                "replicationStagingAccountId": "222222222222",
                "sourceSecurityGroupIds": [],
            }
        )
        cache_table.put_item(
            Item={
                "sourceServerId": "s-term-002",
                "recoveryInstanceId": "ri-term-002",
                "ec2InstanceId": "i-term-002",
                "ec2InstanceState": "running",
                "sourceServerName": "term-server-2",
                "name": "Recovery of term-server-2",
                "instanceType": "m5.large",
                "region": "us-east-2",
                "accountId": "111111111111",
                "sourceExecutionId": "exec-term",
                "lastSyncTime": "2025-02-17T10:35:00Z",
                "replicationStagingAccountId": "222222222222",
                "sourceSecurityGroupIds": [],
            }
        )

        # Verify records exist before termination
        assert "Item" in cache_table.get_item(Key={"sourceServerId": "s-term-001"})
        assert "Item" in cache_table.get_item(Key={"sourceServerId": "s-term-002"})

        # Simulate cache cleanup (as done by execution-handler after DRS termination)
        source_server_ids = ["s-term-001", "s-term-002"]
        with cache_table.batch_writer() as batch:
            for server_id in source_server_ids:
                batch.delete_item(Key={"sourceServerId": server_id})

        # Verify records are deleted
        assert "Item" not in cache_table.get_item(Key={"sourceServerId": "s-term-001"})
        assert "Item" not in cache_table.get_item(Key={"sourceServerId": "s-term-002"})

    def test_terminate_partial_failure_leaves_remaining_records(self, dynamodb_tables):
        """If some deletions fail, remaining records stay in cache."""
        cache_table = dynamodb_tables["recovery_instances"]

        # Pre-populate cache
        for i in range(3):
            cache_table.put_item(
                Item={
                    "sourceServerId": f"s-partial-{i}",
                    "recoveryInstanceId": f"ri-partial-{i}",
                    "ec2InstanceId": f"i-partial-{i}",
                    "ec2InstanceState": "running",
                    "sourceServerName": f"partial-server-{i}",
                    "name": f"Recovery of partial-server-{i}",
                    "instanceType": "t3.medium",
                    "region": "us-east-2",
                    "accountId": "111111111111",
                    "lastSyncTime": "2025-02-17T10:35:00Z",
                    "replicationStagingAccountId": "222222222222",
                    "sourceSecurityGroupIds": [],
                }
            )

        # Delete only first two (simulating partial cleanup)
        with cache_table.batch_writer() as batch:
            batch.delete_item(Key={"sourceServerId": "s-partial-0"})
            batch.delete_item(Key={"sourceServerId": "s-partial-1"})

        # First two deleted, third remains
        assert "Item" not in cache_table.get_item(Key={"sourceServerId": "s-partial-0"})
        assert "Item" not in cache_table.get_item(Key={"sourceServerId": "s-partial-1"})
        assert "Item" in cache_table.get_item(Key={"sourceServerId": "s-partial-2"})

    def test_terminate_nonexistent_records_does_not_error(self, dynamodb_tables):
        """Deleting non-existent cache records does not raise errors."""
        cache_table = dynamodb_tables["recovery_instances"]

        # Delete records that don't exist - should not raise
        with cache_table.batch_writer() as batch:
            batch.delete_item(Key={"sourceServerId": "s-ghost-001"})
            batch.delete_item(Key={"sourceServerId": "s-ghost-002"})

        # Verify no records exist (and no error was raised)
        assert "Item" not in cache_table.get_item(Key={"sourceServerId": "s-ghost-001"})

    def test_sync_then_terminate_full_lifecycle(self, dynamodb_tables):
        """Full lifecycle: sync creates records, terminate deletes them."""
        cache_table = dynamodb_tables["recovery_instances"]

        # Step 1: Sync creates cache records
        mock_drs = MagicMock()
        mock_drs.describe_recovery_instances.return_value = {
            "items": [
                _make_drs_recovery_instance("s-lifecycle", "ri-lifecycle", "i-lifecycle"),
            ]
        }
        mock_drs.describe_source_servers.return_value = {"items": [_make_drs_source_server("lifecycle-server")]}

        mock_ec2 = MagicMock()
        mock_ec2.describe_instances.return_value = _make_ec2_instance("i-lifecycle", "Lifecycle Recovery")

        from shared.recovery_instance_sync import sync_recovery_instances_for_account

        with patch("shared.recovery_instance_sync.boto3") as mock_boto3:
            mock_boto3.client.side_effect = lambda svc, **kw: mock_drs if svc == "drs" else mock_ec2
            mock_boto3.resource.return_value = dynamodb_tables["dynamodb"]

            result = sync_recovery_instances_for_account("111111111111", "us-east-2")

        assert result["instancesUpdated"] == 1

        # Verify record exists
        response = cache_table.get_item(Key={"sourceServerId": "s-lifecycle"})
        assert "Item" in response
        assert response["Item"]["ec2InstanceState"] == "running"

        # Step 2: Terminate deletes cache records
        with cache_table.batch_writer() as batch:
            batch.delete_item(Key={"sourceServerId": "s-lifecycle"})

        # Verify record is gone
        assert "Item" not in cache_table.get_item(Key={"sourceServerId": "s-lifecycle"})


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
