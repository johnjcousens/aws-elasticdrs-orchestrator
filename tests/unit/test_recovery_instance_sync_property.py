"""
Property-based tests for Recovery Instance Sync.

Feature: recovery-instance-sync
Properties:
- Property 1: Sync Idempotency - syncing same data twice produces same DynamoDB state
- Property 2: Data Integrity - all required fields present in every cache record
- Property 3: Timestamp Ordering - lastSyncTime never decreases across syncs
- Property 4: Region Coverage - all configured regions are queried during sync

Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 2.2, 3.1, 3.2, 7.1, 7.5
"""

import os
import sys
import time
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import boto3
import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st
from moto import mock_aws

# Add lambda directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda"))

import shared.recovery_instance_sync as sync_module
from shared.recovery_instance_sync import (
    sync_all_recovery_instances,
    sync_recovery_instances_for_account,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

RECOVERY_INSTANCES_TABLE = "test-prop-recovery-instances"
EXECUTION_HISTORY_TABLE = "test-prop-execution-history"
TARGET_ACCOUNTS_TABLE = "test-prop-target-accounts"
AWS_REGION = "us-east-2"

REQUIRED_CACHE_FIELDS = [
    "sourceServerId",
    "recoveryInstanceId",
    "ec2InstanceId",
    "ec2InstanceState",
    "sourceServerName",
    "name",
    "instanceType",
    "region",
    "accountId",
    "lastSyncTime",
]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_sync_module():
    """Reset shared module globals before each test."""
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
def _set_env(monkeypatch):
    """Set required environment variables."""
    monkeypatch.setenv("RECOVERY_INSTANCES_CACHE_TABLE", RECOVERY_INSTANCES_TABLE)
    monkeypatch.setenv("EXECUTION_HISTORY_TABLE", EXECUTION_HISTORY_TABLE)
    monkeypatch.setenv("TARGET_ACCOUNTS_TABLE", TARGET_ACCOUNTS_TABLE)
    monkeypatch.setenv("AWS_DEFAULT_REGION", AWS_REGION)
    sync_module.RECOVERY_INSTANCES_CACHE_TABLE = RECOVERY_INSTANCES_TABLE
    sync_module.EXECUTION_HISTORY_TABLE = EXECUTION_HISTORY_TABLE
    sync_module.TARGET_ACCOUNTS_TABLE = TARGET_ACCOUNTS_TABLE


# ---------------------------------------------------------------------------
# Hypothesis Strategies
# ---------------------------------------------------------------------------

# Valid AWS-style source server IDs
source_server_id_strategy = st.from_regex(r"^s-[0-9a-f]{17}$", fullmatch=True)

# Valid AWS-style recovery instance IDs
recovery_instance_id_strategy = st.from_regex(r"^ri-[0-9a-f]{17}$", fullmatch=True)

# Valid AWS-style EC2 instance IDs
ec2_instance_id_strategy = st.from_regex(r"^i-[0-9a-f]{17}$", fullmatch=True)

# Valid AWS account IDs (12 digits)
account_id_strategy = st.from_regex(r"^\d{12}$", fullmatch=True)

# Valid AWS regions
aws_region_strategy = st.sampled_from([
    "us-east-1", "us-east-2", "us-west-1", "us-west-2",
    "eu-west-1", "eu-central-1", "ap-southeast-1", "ap-northeast-1",
])

# EC2 instance states
ec2_state_strategy = st.sampled_from(["pending", "running", "stopping", "stopped", "terminated"])

# Instance types
instance_type_strategy = st.sampled_from(["t3.micro", "t3.small", "t3.medium", "m5.large", "c5.xlarge"])


@st.composite
def recovery_instance_strategy(draw):
    """Generate a valid DRS recovery instance as returned by get_recovery_instances_for_region."""
    return {
        "sourceServerId": draw(source_server_id_strategy),
        "recoveryInstanceId": draw(recovery_instance_id_strategy),
        "ec2InstanceId": draw(ec2_instance_id_strategy),
        "ec2InstanceState": draw(ec2_state_strategy),
        "sourceServerName": f"server-{draw(st.integers(min_value=1, max_value=999))}",
        "launchTime": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "region": draw(aws_region_strategy),
        "accountId": draw(account_id_strategy),
        "accountContext": None,
        "replicationStagingAccountId": draw(account_id_strategy),
        "sourceVpcId": f"vpc-{draw(st.from_regex(r'[0-9a-f]{8}', fullmatch=True))}",
        "sourceSubnetId": f"subnet-{draw(st.from_regex(r'[0-9a-f]{8}', fullmatch=True))}",
        "sourceSecurityGroupIds": [f"sg-{draw(st.from_regex(r'[0-9a-f]{8}', fullmatch=True))}"],
        "sourceInstanceProfile": None,
    }


@st.composite
def target_account_strategy(draw):
    """Generate a valid target account with regions."""
    account_id = draw(account_id_strategy)
    regions = draw(st.lists(aws_region_strategy, min_size=1, max_size=4, unique=True))
    return {
        "accountId": account_id,
        "regions": regions,
        "isCurrentAccount": True,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_moto_tables():
    """Create moto DynamoDB tables and return references."""
    dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)

    ri_table = dynamodb.create_table(
        TableName=RECOVERY_INSTANCES_TABLE,
        KeySchema=[{"AttributeName": "sourceServerId", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "sourceServerId", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    dynamodb.create_table(
        TableName=EXECUTION_HISTORY_TABLE,
        KeySchema=[{"AttributeName": "executionId", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "executionId", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    dynamodb.create_table(
        TableName=TARGET_ACCOUNTS_TABLE,
        KeySchema=[{"AttributeName": "accountId", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "accountId", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )

    return ri_table, dynamodb


def _read_all_cache_items(ri_table):
    """Scan all items from the recovery instances cache table."""
    response = ri_table.scan()
    return response.get("Items", [])


def _mock_ec2_details_for_instance(instance):
    """Build EC2 detail dict matching what enrich_with_ec2_details returns."""
    return {
        "Name": f"Recovery of {instance['sourceServerId']}",
        "PrivateIpAddress": "10.0.1.100",
        "PublicIpAddress": None,
        "InstanceType": "t3.medium",
        "LaunchTime": instance.get("launchTime"),
    }



# ===========================================================================
# Property 1: Sync Idempotency
# ===========================================================================


@settings(max_examples=100, deadline=5000)
@given(
    instances=st.lists(recovery_instance_strategy(), min_size=1, max_size=5, unique_by=lambda x: x["sourceServerId"])
)
@pytest.mark.property
def test_property_sync_idempotency(instances):
    """
    Property 1: Syncing the same data twice produces identical DynamoDB state.

    For any set of recovery instances, calling sync_recovery_instances_for_account
    twice with the same DRS response should produce the same set of records in
    DynamoDB (keyed by sourceServerId). Fields other than lastSyncTime must be
    identical across both syncs.

    **Validates: Requirements 1.1, 1.2, 7.1**
    """
    account_id = instances[0]["accountId"]
    region = instances[0]["region"]

    # Force all instances to share the same account/region for a single sync call
    for inst in instances:
        inst["accountId"] = account_id
        inst["region"] = region

    with mock_aws():
        ri_table, dynamodb = _create_moto_tables()

        with (
            patch.object(sync_module, "get_recovery_instances_for_region", return_value=instances),
            patch.object(sync_module, "enrich_with_ec2_details", side_effect=_mock_ec2_details_for_instance),
            patch.object(sync_module, "find_source_execution", return_value={}),
        ):
            # First sync
            sync_recovery_instances_for_account(account_id, region)
            items_after_first = _read_all_cache_items(ri_table)

            # Second sync (same data)
            sync_recovery_instances_for_account(account_id, region)
            items_after_second = _read_all_cache_items(ri_table)

        # Same number of records
        assert len(items_after_first) == len(items_after_second), (
            f"Record count changed: {len(items_after_first)} -> {len(items_after_second)}"
        )

        # Same sourceServerIds present
        ids_first = {item["sourceServerId"] for item in items_after_first}
        ids_second = {item["sourceServerId"] for item in items_after_second}
        assert ids_first == ids_second, f"Server IDs differ: {ids_first} vs {ids_second}"

        # All fields except lastSyncTime must be identical
        first_by_id = {item["sourceServerId"]: item for item in items_after_first}
        second_by_id = {item["sourceServerId"]: item for item in items_after_second}

        for server_id in ids_first:
            r1 = dict(first_by_id[server_id])
            r2 = dict(second_by_id[server_id])
            # Remove lastSyncTime for comparison (timestamps differ between calls)
            r1.pop("lastSyncTime", None)
            r2.pop("lastSyncTime", None)
            assert r1 == r2, f"Records differ for {server_id}: {r1} vs {r2}"


# ===========================================================================
# Property 2: Data Integrity (all required fields present)
# ===========================================================================


@settings(max_examples=100, deadline=5000)
@given(
    instances=st.lists(recovery_instance_strategy(), min_size=1, max_size=5, unique_by=lambda x: x["sourceServerId"])
)
@pytest.mark.property
def test_property_data_integrity(instances):
    """
    Property 2: Every cache record contains all required fields.

    For any set of recovery instances written to DynamoDB via
    sync_recovery_instances_for_account, every resulting record must contain
    all required fields defined in the DynamoDB cache schema.

    **Validates: Requirements 1.1, 1.2, 7.5**
    """
    account_id = instances[0]["accountId"]
    region = instances[0]["region"]

    for inst in instances:
        inst["accountId"] = account_id
        inst["region"] = region

    with mock_aws():
        ri_table, dynamodb = _create_moto_tables()

        with (
            patch.object(sync_module, "get_recovery_instances_for_region", return_value=instances),
            patch.object(sync_module, "enrich_with_ec2_details", side_effect=_mock_ec2_details_for_instance),
            patch.object(sync_module, "find_source_execution", return_value={}),
        ):
            sync_recovery_instances_for_account(account_id, region)

        items = _read_all_cache_items(ri_table)

        # Every record must have all required fields
        for item in items:
            for field in REQUIRED_CACHE_FIELDS:
                assert field in item, f"Missing required field '{field}' in record {item.get('sourceServerId')}"

            # sourceServerId must be non-empty string
            assert isinstance(item["sourceServerId"], str) and len(item["sourceServerId"]) > 0, (
                f"sourceServerId must be non-empty string, got: {item['sourceServerId']}"
            )

            # lastSyncTime must be a valid ISO 8601 timestamp
            last_sync = item["lastSyncTime"]
            assert isinstance(last_sync, str) and len(last_sync) > 0, (
                f"lastSyncTime must be non-empty string, got: {last_sync}"
            )

            # region must be a valid AWS region string
            assert isinstance(item["region"], str) and "-" in item["region"], (
                f"region must be valid AWS region, got: {item['region']}"
            )

            # accountId must be 12 digits
            assert isinstance(item["accountId"], str) and len(item["accountId"]) == 12, (
                f"accountId must be 12-digit string, got: {item['accountId']}"
            )


# ===========================================================================
# Property 3: Timestamp Ordering
# ===========================================================================


@settings(max_examples=100, deadline=5000)
@given(
    instances=st.lists(recovery_instance_strategy(), min_size=1, max_size=3, unique_by=lambda x: x["sourceServerId"])
)
@pytest.mark.property
def test_property_timestamp_ordering(instances):
    """
    Property 3: lastSyncTime never decreases across successive syncs.

    For any set of recovery instances, when sync_recovery_instances_for_account
    is called multiple times, the lastSyncTime on each record must be greater
    than or equal to the previous lastSyncTime.

    **Validates: Requirements 7.5, 3.2**
    """
    account_id = instances[0]["accountId"]
    region = instances[0]["region"]

    for inst in instances:
        inst["accountId"] = account_id
        inst["region"] = region

    with mock_aws():
        ri_table, dynamodb = _create_moto_tables()

        with (
            patch.object(sync_module, "get_recovery_instances_for_region", return_value=instances),
            patch.object(sync_module, "enrich_with_ec2_details", side_effect=_mock_ec2_details_for_instance),
            patch.object(sync_module, "find_source_execution", return_value={}),
        ):
            # First sync
            sync_recovery_instances_for_account(account_id, region)
            items_first = _read_all_cache_items(ri_table)
            first_times = {item["sourceServerId"]: item["lastSyncTime"] for item in items_first}

            # Small delay to ensure timestamp advances
            time.sleep(0.01)

            # Second sync
            sync_recovery_instances_for_account(account_id, region)
            items_second = _read_all_cache_items(ri_table)
            second_times = {item["sourceServerId"]: item["lastSyncTime"] for item in items_second}

        # lastSyncTime must not decrease
        for server_id in first_times:
            t1 = first_times[server_id]
            t2 = second_times[server_id]
            assert t2 >= t1, (
                f"lastSyncTime decreased for {server_id}: {t1} -> {t2}"
            )


# ===========================================================================
# Property 4: Region Coverage
# ===========================================================================


@settings(max_examples=100, deadline=5000)
@given(
    accounts=st.lists(target_account_strategy(), min_size=1, max_size=3, unique_by=lambda x: x["accountId"])
)
@pytest.mark.property
def test_property_region_coverage(accounts):
    """
    Property 4: All configured regions are queried during background sync.

    For any set of target accounts with configured regions,
    sync_all_recovery_instances must call get_recovery_instances_for_region
    for every (account, region) pair.

    **Validates: Requirements 3.1, 3.2**
    """
    # Collect all expected (account, region) pairs
    expected_pairs = set()
    for account in accounts:
        for region in account["regions"]:
            expected_pairs.add((account["accountId"], region))

    # Track which (account, region) pairs were actually queried
    queried_pairs = set()

    def tracking_get_instances(account_id, region, account_context=None):
        queried_pairs.add((account_id, region))
        return []

    with mock_aws():
        ri_table, dynamodb = _create_moto_tables()

        # Seed target accounts table
        ta_table = dynamodb.Table(TARGET_ACCOUNTS_TABLE)
        for account in accounts:
            ta_table.put_item(Item=account)

        with (
            patch.object(sync_module, "get_recovery_instances_for_region", side_effect=tracking_get_instances),
        ):
            sync_all_recovery_instances()

    # Every configured (account, region) pair must have been queried
    assert expected_pairs == queried_pairs, (
        f"Region coverage mismatch.\n"
        f"Expected: {sorted(expected_pairs)}\n"
        f"Queried:  {sorted(queried_pairs)}\n"
        f"Missing:  {sorted(expected_pairs - queried_pairs)}\n"
        f"Extra:    {sorted(queried_pairs - expected_pairs)}"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
