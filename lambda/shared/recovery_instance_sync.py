"""
Recovery Instance Sync Service for DRS Recovery Instance Caching

This module provides core functionality for syncing DRS recovery instance data
to DynamoDB cache to optimize Recovery Plans page load performance. It reduces
page load time from 20+ seconds to under 3 seconds by caching recovery instance
data with two sync mechanisms:

1. Wave Completion Sync: Immediate sync after wave execution completes
2. Background Sync: EventBridge-triggered sync every 5 minutes

Key Functions:
    - sync_all_recovery_instances(): Main sync function for EventBridge trigger
    - sync_recovery_instances_for_account(): Single account/region sync
    - get_recovery_instances_for_region(): Query DRS for recovery instances
    - enrich_with_ec2_details(): Add EC2 instance details
    - find_source_execution(): Find source execution from history
    - get_recovery_instance_sync_status(): Get last sync status

Error Classes:
    - RecoveryInstanceSyncError: Base exception for sync errors
    - RecoveryInstanceSyncTimeoutError: Sync operation timeout
    - RecoveryInstanceSyncValidationError: Validation failure

Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5
"""

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Environment variables
RECOVERY_INSTANCES_CACHE_TABLE = os.environ.get("RECOVERY_INSTANCES_CACHE_TABLE")
EXECUTION_HISTORY_TABLE = os.environ.get("EXECUTION_HISTORY_TABLE")
TARGET_ACCOUNTS_TABLE = os.environ.get("TARGET_ACCOUNTS_TABLE")

# DynamoDB resource (lazy initialization)
_dynamodb = None
_recovery_instances_table = None
_execution_history_table = None
_target_accounts_table = None


def _get_dynamodb_resource():
    """Get or create DynamoDB resource."""
    global _dynamodb
    if _dynamodb is None:
        _dynamodb = boto3.resource("dynamodb")
    return _dynamodb


def _get_recovery_instances_table():
    """Get or create recovery instances cache table reference."""
    global _recovery_instances_table
    if _recovery_instances_table is None:
        if not RECOVERY_INSTANCES_CACHE_TABLE:
            raise RecoveryInstanceSyncError("RECOVERY_INSTANCES_CACHE_TABLE environment variable not set")
        dynamodb = _get_dynamodb_resource()
        _recovery_instances_table = dynamodb.Table(RECOVERY_INSTANCES_CACHE_TABLE)
    return _recovery_instances_table


def _get_execution_history_table():
    """Get or create execution history table reference."""
    global _execution_history_table
    if _execution_history_table is None:
        if not EXECUTION_HISTORY_TABLE:
            raise RecoveryInstanceSyncError("EXECUTION_HISTORY_TABLE environment variable not set")
        dynamodb = _get_dynamodb_resource()
        _execution_history_table = dynamodb.Table(EXECUTION_HISTORY_TABLE)
    return _execution_history_table


def _get_target_accounts_table():
    """Get or create target accounts table reference."""
    global _target_accounts_table
    if _target_accounts_table is None:
        if not TARGET_ACCOUNTS_TABLE:
            raise RecoveryInstanceSyncError("TARGET_ACCOUNTS_TABLE environment variable not set")
        dynamodb = _get_dynamodb_resource()
        _target_accounts_table = dynamodb.Table(TARGET_ACCOUNTS_TABLE)
    return _target_accounts_table


class RecoveryInstanceSyncError(Exception):
    """Base exception for recovery instance sync errors."""

    pass


class RecoveryInstanceSyncTimeoutError(RecoveryInstanceSyncError):
    """Raised when sync operation exceeds timeout."""

    pass


class RecoveryInstanceSyncValidationError(RecoveryInstanceSyncError):
    """Raised when validation fails."""

    pass


def sync_all_recovery_instances() -> Dict[str, Any]:
    """
    Background sync of recovery instances across all target accounts and regions.
    Called by data-management-handler (invoked directly by EventBridge or API).

    Performs DRS/EC2 API calls and writes results to DynamoDB cache.

    Returns:
        Dict with sync results: instancesUpdated, regionsScanned, errors

    Example:
        >>> result = sync_all_recovery_instances()
        >>> result["instancesUpdated"]
        42

    Validates: Requirements 1.3 (background sync)
    """
    logger.info("Starting background recovery instance sync")

    # Get all target accounts and their regions
    target_accounts = _get_target_accounts()

    # Query DRS for all recovery instances across accounts/regions
    all_instances = []
    errors = []
    regions_scanned = 0

    for account in target_accounts:
        account_id = account.get("accountId")
        regions = account.get("regions", [])

        for region in regions:
            regions_scanned += 1
            try:
                instances = get_recovery_instances_for_region(account_id, region, account)
                all_instances.extend(instances)
                logger.info(f"Found {len(instances)} recovery instances in {account_id}/{region}")
            except Exception as e:
                error_msg = f"Failed to sync {account_id}/{region}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                errors.append(error_msg)
                # Continue with other accounts/regions

    # Enrich with EC2 details and find source executions
    enriched_instances = []
    for instance in all_instances:
        try:
            # Enrich with EC2 details
            ec2_details = enrich_with_ec2_details(
                instance["ec2InstanceId"], instance["region"], instance["accountId"], instance.get("accountContext")
            )

            # Find source execution from history
            source_execution = find_source_execution(instance["sourceServerId"], instance.get("launchTime"))

            # Build enriched instance record
            enriched_instance = {
                "sourceServerId": instance["sourceServerId"],
                "recoveryInstanceId": instance["recoveryInstanceId"],
                "ec2InstanceId": instance["ec2InstanceId"],
                "ec2InstanceState": instance["ec2InstanceState"],
                "sourceServerName": instance.get("sourceServerName", instance["sourceServerId"]),
                "name": ec2_details.get("Name", f"Recovery of {instance['sourceServerId']}"),
                "privateIp": ec2_details.get("PrivateIpAddress"),
                "publicIp": ec2_details.get("PublicIpAddress"),
                "instanceType": ec2_details.get("InstanceType", "unknown"),
                "launchTime": instance.get("launchTime"),
                "region": instance["region"],
                "accountId": instance["accountId"],
                "sourceExecutionId": source_execution.get("executionId"),
                "sourcePlanName": source_execution.get("planName"),
                "lastSyncTime": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "replicationStagingAccountId": instance.get("replicationStagingAccountId"),
                "sourceVpcId": instance.get("sourceVpcId"),
                "sourceSubnetId": instance.get("sourceSubnetId"),
                "sourceSecurityGroupIds": instance.get("sourceSecurityGroupIds", []),
                "sourceInstanceProfile": instance.get("sourceInstanceProfile"),
            }
            enriched_instances.append(enriched_instance)

        except Exception as e:
            error_msg = f"Failed to enrich instance {instance.get('recoveryInstanceId', 'unknown')}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            errors.append(error_msg)
            # Continue with other instances

    # Update DynamoDB cache
    if enriched_instances:
        try:
            table = _get_recovery_instances_table()
            with table.batch_writer() as batch:
                for instance in enriched_instances:
                    batch.put_item(Item=instance)
            logger.info(f"Wrote {len(enriched_instances)} instances to cache")
        except Exception as e:
            error_msg = f"Failed to write to DynamoDB cache: {str(e)}"
            logger.error(error_msg, exc_info=True)
            errors.append(error_msg)

    logger.info(f"Background sync completed: {len(enriched_instances)} instances updated, {regions_scanned} regions")

    return {"instancesUpdated": len(enriched_instances), "regionsScanned": regions_scanned, "errors": errors}


def sync_recovery_instances_for_account(account_id: str, region: str, account_context: Optional[Dict] = None) -> Dict:
    """
    Sync recovery instances for a single account/region.

    Args:
        account_id: AWS account ID
        region: AWS region
        account_context: Cross-account context (optional)

    Returns:
        Dict with sync results: instancesUpdated, errors

    Example:
        >>> result = sync_recovery_instances_for_account("891376951562", "us-east-2")
        >>> result["instancesUpdated"]
        5

    Validates: Requirements 1.2 (wave completion sync)
    """
    logger.info(f"Syncing recovery instances for account {account_id} in region {region}")

    errors = []

    try:
        # Get recovery instances for this account/region
        instances = get_recovery_instances_for_region(account_id, region, account_context)
        logger.info(f"Found {len(instances)} recovery instances in {account_id}/{region}")

        # Enrich with EC2 details and find source executions
        enriched_instances = []
        for instance in instances:
            try:
                # Enrich with EC2 details
                ec2_details = enrich_with_ec2_details(
                    instance["ec2InstanceId"], instance["region"], instance["accountId"], instance.get("accountContext")
                )

                # Find source execution from history
                source_execution = find_source_execution(instance["sourceServerId"], instance.get("launchTime"))

                # Build enriched instance record
                enriched_instance = {
                    "sourceServerId": instance["sourceServerId"],
                    "recoveryInstanceId": instance["recoveryInstanceId"],
                    "ec2InstanceId": instance["ec2InstanceId"],
                    "ec2InstanceState": instance["ec2InstanceState"],
                    "sourceServerName": instance.get("sourceServerName", instance["sourceServerId"]),
                    "name": ec2_details.get("Name", f"Recovery of {instance['sourceServerId']}"),
                    "privateIp": ec2_details.get("PrivateIpAddress"),
                    "publicIp": ec2_details.get("PublicIpAddress"),
                    "instanceType": ec2_details.get("InstanceType", "unknown"),
                    "launchTime": instance.get("launchTime"),
                    "region": instance["region"],
                    "accountId": instance["accountId"],
                    "sourceExecutionId": source_execution.get("executionId"),
                    "sourcePlanName": source_execution.get("planName"),
                    "lastSyncTime": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "replicationStagingAccountId": instance.get("replicationStagingAccountId"),
                    "sourceVpcId": instance.get("sourceVpcId"),
                    "sourceSubnetId": instance.get("sourceSubnetId"),
                    "sourceSecurityGroupIds": instance.get("sourceSecurityGroupIds", []),
                    "sourceInstanceProfile": instance.get("sourceInstanceProfile"),
                }
                enriched_instances.append(enriched_instance)

            except Exception as e:
                error_msg = f"Failed to enrich instance {instance.get('recoveryInstanceId', 'unknown')}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                errors.append(error_msg)
                # Continue with other instances

        # Update DynamoDB cache
        if enriched_instances:
            try:
                table = _get_recovery_instances_table()
                with table.batch_writer() as batch:
                    for instance in enriched_instances:
                        batch.put_item(Item=instance)
                logger.info(f"Wrote {len(enriched_instances)} instances to cache")
            except Exception as e:
                error_msg = f"Failed to write to DynamoDB cache: {str(e)}"
                logger.error(error_msg, exc_info=True)
                errors.append(error_msg)

        return {"instancesUpdated": len(enriched_instances), "errors": errors}

    except Exception as e:
        error_msg = f"Failed to sync {account_id}/{region}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {"instancesUpdated": 0, "errors": [error_msg]}


def get_recovery_instances_for_region(
    account_id: str, region: str, account_context: Optional[Dict] = None
) -> List[Dict]:
    """
    Query DRS for recovery instances in a specific region.

    Handles pagination and cross-account access.

    Args:
        account_id: AWS account ID
        region: AWS region
        account_context: Cross-account context (optional)

    Returns:
        List of recovery instance dictionaries

    Example:
        >>> instances = get_recovery_instances_for_region("891376951562", "us-east-2")
        >>> len(instances)
        5

    Validates: Requirements 1.3 (DRS API queries)
    """
    logger.info(f"Querying DRS for recovery instances in {account_id}/{region}")

    # Get DRS client (with cross-account support if needed)
    try:
        if account_context and not account_context.get("isCurrentAccount", True):
            drs_client = _get_cross_account_drs_client(region, account_context)
        else:
            drs_client = boto3.client("drs", region_name=region)
    except Exception as e:
        error_msg = f"Failed to create DRS client for {account_id}/{region}: {str(e)}"
        logger.error(error_msg)
        raise RecoveryInstanceSyncError(error_msg)

    # Query DRS with pagination
    instances = []
    next_token = None

    try:
        while True:
            # Build request parameters
            params = {}
            if next_token:
                params["nextToken"] = next_token

            # Query DRS
            response = drs_client.describe_recovery_instances(**params)

            # Process items
            for item in response.get("items", []):
                # Extract recovery instance data
                instance = {
                    "sourceServerId": item.get("sourceServerID"),
                    "recoveryInstanceId": item.get("recoveryInstanceID"),
                    "ec2InstanceId": item.get("ec2InstanceID"),
                    "ec2InstanceState": item.get("ec2InstanceState", "unknown"),
                    "launchTime": item.get("launchTime"),
                    "region": region,
                    "accountId": account_id,
                    "accountContext": account_context,
                }

                # Get source server details for name and replication config
                try:
                    source_server = drs_client.describe_source_servers(
                        filters={"sourceServerIDs": [item.get("sourceServerID")]}
                    )
                    if source_server.get("items"):
                        server_data = source_server["items"][0]
                        instance["sourceServerName"] = server_data.get("sourceProperties", {}).get("hostname")
                        instance["replicationStagingAccountId"] = server_data.get("stagingArea", {}).get(
                            "stagingAccountID"
                        )

                        # Extract source infrastructure configuration
                        source_props = server_data.get("sourceProperties", {})
                        network_interfaces = source_props.get("networkInterfaces", [])
                        if network_interfaces:
                            primary_interface = network_interfaces[0]
                            instance["sourceVpcId"] = primary_interface.get("vpcId")
                            instance["sourceSubnetId"] = primary_interface.get("subnetId")
                            instance["sourceSecurityGroupIds"] = primary_interface.get("securityGroupIds", [])

                        # Extract IAM instance profile
                        instance["sourceInstanceProfile"] = source_props.get("iamInstanceProfileArn")

                except Exception as e:
                    logger.warning(f"Failed to get source server details for {item.get('sourceServerID')}: {e}")

                instances.append(instance)

            # Check for more pages
            next_token = response.get("nextToken")
            if not next_token:
                break

        logger.info(f"Found {len(instances)} recovery instances in {account_id}/{region}")
        return instances

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        error_msg = e.response.get("Error", {}).get("Message", "")
        logger.error(f"DRS API error ({error_code}): {error_msg}")
        raise RecoveryInstanceSyncError(f"DRS API error ({error_code}): {error_msg}")
    except Exception as e:
        logger.error(f"Unexpected error querying DRS: {str(e)}", exc_info=True)
        raise RecoveryInstanceSyncError(f"Unexpected error querying DRS: {str(e)}")


def enrich_with_ec2_details(
    ec2_instance_id: str, region: str, account_id: str, account_context: Optional[Dict] = None
) -> Dict:
    """
    Add EC2 instance details to recovery instance data.

    Queries EC2 API for instance details including Name tag, IPs, instance type.

    Args:
        ec2_instance_id: EC2 instance ID
        region: AWS region
        account_id: AWS account ID
        account_context: Cross-account context (optional)

    Returns:
        Dict with EC2 details: Name, PrivateIpAddress, PublicIpAddress, InstanceType

    Example:
        >>> details = enrich_with_ec2_details("i-1234567890abcdef0", "us-east-2", "891376951562")
        >>> details["InstanceType"]
        't3.medium'

    Validates: Requirements 1.3 (EC2 enrichment)
    """
    logger.debug(f"Enriching EC2 details for {ec2_instance_id} in {account_id}/{region}")

    # Get EC2 client (with cross-account support if needed)
    try:
        if account_context and not account_context.get("isCurrentAccount", True):
            ec2_client = _get_cross_account_ec2_client(region, account_context)
        else:
            ec2_client = boto3.client("ec2", region_name=region)
    except Exception as e:
        logger.warning(f"Failed to create EC2 client for {account_id}/{region}: {e}")
        return {"Name": f"Recovery instance {ec2_instance_id}", "InstanceType": "unknown"}

    # Query EC2 for instance details
    try:
        response = ec2_client.describe_instances(InstanceIds=[ec2_instance_id])

        if not response.get("Reservations"):
            logger.warning(f"EC2 instance {ec2_instance_id} not found")
            return {"Name": f"Recovery instance {ec2_instance_id}", "InstanceType": "unknown"}

        instance = response["Reservations"][0]["Instances"][0]

        # Extract Name tag
        name = None
        for tag in instance.get("Tags", []):
            if tag.get("Key") == "Name":
                name = tag.get("Value")
                break

        # Build EC2 details
        ec2_details = {
            "Name": name or f"Recovery instance {ec2_instance_id}",
            "PrivateIpAddress": instance.get("PrivateIpAddress"),
            "PublicIpAddress": instance.get("PublicIpAddress"),
            "InstanceType": instance.get("InstanceType", "unknown"),
            "LaunchTime": instance.get("LaunchTime").isoformat() if instance.get("LaunchTime") else None,
        }

        return ec2_details

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        logger.warning(f"EC2 API error ({error_code}) for {ec2_instance_id}: {e}")
        return {"Name": f"Recovery instance {ec2_instance_id}", "InstanceType": "unknown"}
    except Exception as e:
        logger.warning(f"Unexpected error querying EC2 for {ec2_instance_id}: {e}")
        return {"Name": f"Recovery instance {ec2_instance_id}", "InstanceType": "unknown"}


def find_source_execution(source_server_id: str, launch_time: Optional[str] = None) -> Dict:
    """
    Find source execution from execution history.

    Scans execution history to find which execution created this recovery instance.

    Args:
        source_server_id: DRS source server ID
        launch_time: Instance launch time (ISO format, optional)

    Returns:
        Dict with executionId and planName, or empty dict if not found

    Example:
        >>> execution = find_source_execution("s-1234567890abcdef0", "2025-02-17T10:30:00Z")
        >>> execution["executionId"]
        'exec-abc123'

    Validates: Requirements 1.3 (execution tracking)
    """
    logger.debug(f"Finding source execution for server {source_server_id}")

    try:
        table = _get_execution_history_table()

        # Scan execution history for this server
        # Note: This is not optimal but execution history table doesn't have
        # a GSI on source server ID. Consider adding one in future optimization.
        response = table.scan(
            FilterExpression="contains(sourceServerIds, :server_id)",
            ExpressionAttributeValues={":server_id": source_server_id},
            Limit=10,  # Limit to recent executions
        )

        if not response.get("Items"):
            logger.debug(f"No execution found for server {source_server_id}")
            return {}

        # If we have launch time, find the execution closest to it
        if launch_time:
            # Convert launch time to timestamp for comparison
            try:
                from dateutil import parser

                launch_dt = parser.parse(launch_time)
                launch_timestamp = launch_dt.timestamp()

                # Find execution with closest start time
                closest_execution = None
                min_time_diff = float("inf")

                for item in response["Items"]:
                    exec_start_time = item.get("startTime")
                    if exec_start_time:
                        exec_dt = parser.parse(exec_start_time)
                        exec_timestamp = exec_dt.timestamp()
                        time_diff = abs(launch_timestamp - exec_timestamp)

                        if time_diff < min_time_diff:
                            min_time_diff = time_diff
                            closest_execution = item

                if closest_execution:
                    return {
                        "executionId": closest_execution.get("executionId"),
                        "planName": closest_execution.get("planName"),
                    }
            except Exception as e:
                logger.warning(f"Failed to parse launch time {launch_time}: {e}")

        # If no launch time or parsing failed, return most recent execution
        items = response["Items"]
        if items:
            # Sort by start time descending
            items.sort(key=lambda x: x.get("startTime", ""), reverse=True)
            return {"executionId": items[0].get("executionId"), "planName": items[0].get("planName")}

        return {}

    except Exception as e:
        logger.warning(f"Failed to find source execution for {source_server_id}: {e}")
        return {}


def get_recovery_instance_sync_status() -> Dict:
    """
    Get last sync status from DynamoDB.

    Returns:
        Dict with last sync status: lastSyncTime, instancesUpdated, errors

    Example:
        >>> status = get_recovery_instance_sync_status()
        >>> status["lastSyncTime"]
        '2025-02-17T10:35:00Z'

    Validates: Requirements 2.2 (status retrieval)
    """
    logger.info("Getting recovery instance sync status")

    try:
        table = _get_recovery_instances_table()

        # Query for most recent sync record
        # Note: This is a simple implementation that scans for the most recent lastSyncTime
        # In production, consider adding a dedicated status record or GSI
        response = table.scan(Limit=1, ProjectionExpression="lastSyncTime")

        if response.get("Items"):
            last_sync_time = response["Items"][0].get("lastSyncTime")

            # Count total instances in cache
            count_response = table.scan(Select="COUNT")
            instance_count = count_response.get("Count", 0)

            return {
                "lastSyncTime": last_sync_time,
                "instancesUpdated": instance_count,
                "errors": [],
                "status": "healthy",
            }
        else:
            return {
                "lastSyncTime": None,
                "instancesUpdated": 0,
                "errors": [],
                "status": "no_sync_yet",
            }

    except Exception as e:
        logger.error(f"Failed to get sync status: {str(e)}", exc_info=True)
        return {"lastSyncTime": None, "instancesUpdated": 0, "errors": [str(e)], "status": "error"}


def _get_target_accounts() -> List[Dict]:
    """
    Get all target accounts from DynamoDB.

    Returns:
        List of target account dictionaries with accountId and regions

    Raises:
        RecoveryInstanceSyncError: If query fails
    """
    try:
        table = _get_target_accounts_table()
        response = table.scan()

        accounts = []
        for item in response.get("Items", []):
            accounts.append(
                {"accountId": item.get("accountId"), "regions": item.get("regions", []), "accountContext": item}
            )

        logger.info(f"Found {len(accounts)} target accounts")
        return accounts

    except Exception as e:
        error_msg = f"Failed to get target accounts: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise RecoveryInstanceSyncError(error_msg)


def _get_cross_account_drs_client(region: str, account_context: Dict):
    """
    Get DRS client for cross-account operations.

    Args:
        region: AWS region
        account_context: Dict with account details including role info

    Returns:
        boto3 DRS client with assumed role credentials

    Raises:
        RecoveryInstanceSyncError: When role assumption fails
    """
    try:
        from shared.cross_account import get_cross_account_session

        account_id = account_context["accountId"]
        assume_role_name = account_context.get("assumeRoleName")

        if not assume_role_name:
            # No role to assume, use current credentials
            return boto3.client("drs", region_name=region)

        role_arn = f"arn:aws:iam::{account_id}:role/{assume_role_name}"
        external_id = account_context.get("externalId")

        session = get_cross_account_session(role_arn, external_id)
        drs_client = session.client("drs", region_name=region)

        logger.info(f"Created cross-account DRS client for account {account_id}")
        return drs_client

    except Exception as e:
        error_msg = f"Failed to create cross-account DRS client: {str(e)}"
        logger.error(error_msg)
        raise RecoveryInstanceSyncError(error_msg)


def _get_cross_account_ec2_client(region: str, account_context: Dict):
    """
    Get EC2 client for cross-account operations.

    Args:
        region: AWS region
        account_context: Dict with account details including role info

    Returns:
        boto3 EC2 client with assumed role credentials

    Raises:
        RecoveryInstanceSyncError: When role assumption fails
    """
    try:
        from shared.cross_account import get_cross_account_session

        account_id = account_context["accountId"]
        assume_role_name = account_context.get("assumeRoleName")

        if not assume_role_name:
            # No role to assume, use current credentials
            return boto3.client("ec2", region_name=region)

        role_arn = f"arn:aws:iam::{account_id}:role/{assume_role_name}"
        external_id = account_context.get("externalId")

        session = get_cross_account_session(role_arn, external_id)
        ec2_client = session.client("ec2", region_name=region)

        logger.info(f"Created cross-account EC2 client for account {account_id}")
        return ec2_client

    except Exception as e:
        error_msg = f"Failed to create cross-account EC2 client: {str(e)}"
        logger.error(error_msg)
        raise RecoveryInstanceSyncError(error_msg)
