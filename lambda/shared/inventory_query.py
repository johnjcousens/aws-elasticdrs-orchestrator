"""
Inventory Database Query Module

Provides fast access to source server inventory data from DynamoDB,
reducing DRS API calls by 90% for operations that can use cached data.

The inventory database is synced every 15 minutes from DRS and EC2 APIs,
containing comprehensive server information including hardware specs,
network configuration, tags, and replication state.

Key Functions:
- query_inventory_by_regions(): Query inventory for specified regions
- is_inventory_fresh(): Check if inventory data is current
- get_inventory_table(): Get DynamoDB table resource

Usage:
    from shared.inventory_query import query_inventory_by_regions

    servers = query_inventory_by_regions(
        regions=['us-east-1', 'us-west-2'],
        filters={'replicationState': 'CONTINUOUS'}
    )
"""

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import boto3
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Environment variables
SOURCE_SERVER_INVENTORY_TABLE = os.environ.get("SOURCE_SERVER_INVENTORY_TABLE")

# DynamoDB client (lazy initialization)
dynamodb = boto3.resource("dynamodb")
_inventory_table = None

# CloudWatch client (lazy initialization)
cloudwatch = boto3.client("cloudwatch")

# DRS client (lazy initialization per region)
_drs_clients = {}

# Freshness threshold (15 minutes - matches sync interval)
INVENTORY_FRESHNESS_MINUTES = 15


def get_inventory_table():
    """
    Get or initialize source server inventory table.

    Returns:
        DynamoDB Table resource or None if not configured
    """
    global _inventory_table
    if _inventory_table is None:
        if SOURCE_SERVER_INVENTORY_TABLE:
            _inventory_table = dynamodb.Table(SOURCE_SERVER_INVENTORY_TABLE)
        else:
            logger.warning("SOURCE_SERVER_INVENTORY_TABLE environment variable not set")
    return _inventory_table


def publish_metric(metric_name: str, value: float, unit: str = "Count") -> None:
    """
    Publish custom CloudWatch metric for inventory database usage.

    Publishes metrics to the DRSOrchestration/ActiveRegionFiltering namespace
    for monitoring inventory database hits and misses.

    Args:
        metric_name: Name of the metric (e.g., 'InventoryDatabaseHits')
        value: Metric value to publish
        unit: CloudWatch unit (default: 'Count')

    Example:
        >>> publish_metric('InventoryDatabaseHits', 1)
        >>> publish_metric('InventoryDatabaseMisses', 1)
    """
    try:
        cloudwatch.put_metric_data(
            Namespace="DRSOrchestration/ActiveRegionFiltering",
            MetricData=[{"MetricName": metric_name, "Value": value, "Unit": unit}],
        )
        logger.debug(f"Published CloudWatch metric: {metric_name}={value} {unit}")
    except Exception as e:
        logger.warning(f"Failed to publish CloudWatch metric {metric_name}: {e}")


def _get_drs_client(region: str):
    """
    Get or initialize DRS client for specified region.

    Args:
        region: AWS region name

    Returns:
        boto3 DRS client for the region
    """
    global _drs_clients
    if region not in _drs_clients:
        _drs_clients[region] = boto3.client("drs", region_name=region)
    return _drs_clients[region]


def is_inventory_fresh(
    max_age_minutes: int = INVENTORY_FRESHNESS_MINUTES,
) -> bool:
    """
    Check if inventory database contains fresh data.

    Queries the inventory table for the most recent lastUpdated timestamp
    and compares it to the current time. Data is considered fresh if it
    was updated within the specified time window.

    Args:
        max_age_minutes: Maximum age in minutes to consider fresh (default: 15)

    Returns:
        True if inventory was updated within max_age_minutes, False otherwise

    Example:
        >>> if is_inventory_fresh():
        ...     servers = query_inventory_by_regions(['us-east-1'])
        ... else:
        ...     servers = query_drs_api_directly(['us-east-1'])
    """
    inventory_table = get_inventory_table()

    if not inventory_table:
        logger.warning("Inventory table not configured")
        return False

    try:
        # Query for any record to check lastUpdated timestamp
        # Use limit=1 for efficiency - we only need one record
        response = inventory_table.scan(Limit=1)

        items = response.get("Items", [])
        if not items:
            logger.debug("Inventory table is empty")
            return False

        # Get the lastUpdated timestamp from the first item
        last_updated_str = items[0].get("lastUpdated")
        if not last_updated_str:
            logger.warning("Inventory record missing lastUpdated timestamp")
            return False

        # Parse ISO timestamp
        last_updated = datetime.fromisoformat(last_updated_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        age = now - last_updated

        is_fresh = age.total_seconds() < (max_age_minutes * 60)

        if is_fresh:
            logger.debug(
                f"Inventory is fresh (age: {age.total_seconds():.0f}s, " f"threshold: {max_age_minutes * 60}s)"
            )
        else:
            logger.info(f"Inventory is stale (age: {age.total_seconds():.0f}s, " f"threshold: {max_age_minutes * 60}s)")

        return is_fresh

    except ClientError as e:
        logger.error(f"DynamoDB error checking inventory freshness: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error checking inventory freshness: {e}")
        return False


def query_inventory_by_regions(
    regions: List[str], filters: Optional[Dict[str, Any]] = None, update_on_fallback: bool = False
) -> List[Dict[str, Any]]:
    """
    Query source server inventory database for specified regions.

    Provides fast access to server data without DRS API calls.
    Falls back to empty list if inventory is stale or unavailable
    (caller should handle fallback to DRS API).

    OPTIMIZATION: When update_on_fallback=True and inventory is stale,
    this function will query DRS API directly and update the inventory
    database before returning results.

    Args:
        regions: List of AWS regions to query (e.g., ['us-east-1', 'us-west-2'])
        filters: Optional filters to apply:
            - hostname: Filter by hostname (exact match)
            - replicationState: Filter by replication state (e.g., 'CONTINUOUS')
            - stagingAccountId: Filter by staging account ID
            - sourceAccountId: Filter by source account ID
            - minCpuCores: Minimum CPU cores
            - minRamBytes: Minimum RAM in bytes
        update_on_fallback: If True, query DRS API and update inventory when stale

    Returns:
        List of server dictionaries in frontend-compatible format.
        Returns empty list if inventory is unavailable or stale (unless update_on_fallback=True).

    Example:
        >>> servers = query_inventory_by_regions(
        ...     regions=['us-east-1', 'us-west-2'],
        ...     filters={'replicationState': 'CONTINUOUS'}
        ... )
        >>> print(f"Found {len(servers)} servers")
        Found 42 servers
    """
    inventory_table = get_inventory_table()

    if not inventory_table:
        logger.warning("Inventory table not configured, returning empty list")
        return []

    # Check if inventory is fresh before querying
    if not is_inventory_fresh():
        if update_on_fallback:
            logger.info("Inventory is stale, falling back to DRS API and updating database")
            return _fallback_to_drs_api_and_update(regions, filters)
        else:
            logger.warning("Inventory is stale, returning empty list for DRS API fallback")
            return []

    try:
        # Build filter expression for regions
        filter_expression = Attr("replicationRegion").is_in(regions)

        # Add optional filters
        if filters:
            if "hostname" in filters:
                filter_expression &= Attr("hostname").eq(filters["hostname"])

            if "replicationState" in filters:
                filter_expression &= Attr("replicationState").eq(filters["replicationState"])

            if "stagingAccountId" in filters:
                filter_expression &= Attr("stagingAccountId").eq(filters["stagingAccountId"])

            if "sourceAccountId" in filters:
                filter_expression &= Attr("sourceAccountId").eq(filters["sourceAccountId"])

            if "minCpuCores" in filters:
                filter_expression &= Attr("cpuCores").gte(filters["minCpuCores"])

            if "minRamBytes" in filters:
                filter_expression &= Attr("ramBytes").gte(filters["minRamBytes"])

        # Query DynamoDB with filter
        logger.debug(f"Querying inventory for {len(regions)} regions with filters: {filters}")
        response = inventory_table.scan(FilterExpression=filter_expression)

        servers = response.get("Items", [])

        # Handle pagination (inventory table can be large)
        while "LastEvaluatedKey" in response:
            response = inventory_table.scan(
                FilterExpression=filter_expression,
                ExclusiveStartKey=response["LastEvaluatedKey"],
            )
            servers.extend(response.get("Items", []))

        # Deduplicate servers by sourceServerID (keep most recent by lastUpdatedDateTime)
        seen_servers = {}
        for server in servers:
            server_id = server.get("sourceServerID")
            if not server_id:
                continue

            # Keep the server with the most recent lastUpdatedDateTime
            if server_id not in seen_servers:
                seen_servers[server_id] = server
            else:
                existing_time = seen_servers[server_id].get("lastUpdatedDateTime", "")
                new_time = server.get("lastUpdatedDateTime", "")
                if new_time > existing_time:
                    seen_servers[server_id] = server

        deduplicated_servers = list(seen_servers.values())

        if len(servers) != len(deduplicated_servers):
            logger.warning(
                f"Deduplicated {len(servers)} servers to {len(deduplicated_servers)} "
                f"(removed {len(servers) - len(deduplicated_servers)} duplicates)"
            )

        logger.info(
            f"Retrieved {len(deduplicated_servers)} unique servers from inventory database for {len(regions)} regions"
        )

        # Publish CloudWatch metric for inventory database hit
        publish_metric("InventoryDatabaseHits", 1)

        return deduplicated_servers

    except ClientError as e:
        logger.error(f"DynamoDB error querying inventory: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error querying inventory: {e}")
        return []


def query_inventory_by_staging_account(
    staging_account_id: str, regions: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Query inventory for servers in a specific staging account.

    Optimized query using stagingAccountId filter, optionally
    limited to specific regions.

    Args:
        staging_account_id: AWS account ID of staging account
        regions: Optional list of regions to filter by

    Returns:
        List of server dictionaries for the staging account

    Example:
        >>> servers = query_inventory_by_staging_account(
        ...     staging_account_id='123456789012',
        ...     regions=['us-east-1', 'us-west-2']
        ... )
    """
    inventory_table = get_inventory_table()

    if not inventory_table:
        logger.warning("Inventory table not configured, returning empty list")
        return []

    if not is_inventory_fresh():
        logger.warning("Inventory is stale, returning empty list for DRS API fallback")
        return []

    try:
        # Build filter expression
        filter_expression = Attr("stagingAccountId").eq(staging_account_id)

        if regions:
            filter_expression &= Attr("replicationRegion").is_in(regions)

        logger.debug(f"Querying inventory for staging account {staging_account_id}")
        response = inventory_table.scan(FilterExpression=filter_expression)

        servers = response.get("Items", [])

        # Handle pagination
        while "LastEvaluatedKey" in response:
            response = inventory_table.scan(
                FilterExpression=filter_expression,
                ExclusiveStartKey=response["LastEvaluatedKey"],
            )
            servers.extend(response.get("Items", []))

        logger.info(
            f"Retrieved {len(servers)} servers from inventory database " f"for staging account {staging_account_id}"
        )

        return servers

    except ClientError as e:
        logger.error(f"DynamoDB error querying inventory by staging account: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error querying inventory by staging account: {e}")
        return []


def get_server_by_id(source_server_id: str, replication_region: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Get a single server by sourceServerID.

    Uses DynamoDB GetItem for efficient single-record retrieval.
    If replication_region is not provided, scans for the server.

    Args:
        source_server_id: DRS source server ID (e.g., 's-1234567890abcdef0')
        replication_region: Optional replication region for direct lookup

    Returns:
        Server dictionary or None if not found

    Example:
        >>> server = get_server_by_id('s-1234567890abcdef0', 'us-east-1')
        >>> if server:
        ...     print(f"Found server: {server['hostname']}")
    """
    inventory_table = get_inventory_table()

    if not inventory_table:
        logger.warning("Inventory table not configured")
        return None

    if not is_inventory_fresh():
        logger.warning("Inventory is stale, returning None for DRS API fallback")
        return None

    try:
        if replication_region:
            # Direct GetItem using primary key (most efficient)
            response = inventory_table.get_item(
                Key={
                    "sourceServerID": source_server_id,
                    "replicationRegion": replication_region,
                }
            )
            return response.get("Item")
        else:
            # Scan for server (less efficient but works without region)
            response = inventory_table.scan(
                FilterExpression=Attr("sourceServerID").eq(source_server_id),
                Limit=1,
            )
            items = response.get("Items", [])
            return items[0] if items else None

    except ClientError as e:
        logger.error(f"DynamoDB error getting server by ID: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error getting server by ID: {e}")
        return None


def get_failback_topology(source_server_id: str, replication_region: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve original replication topology for failback operations.

    During disaster recovery failback, the DRS agent must be reinstalled on
    recovered servers. This function retrieves the original source region,
    account ID, and replication configuration to guide agent installation.

    Args:
        source_server_id: DRS source server ID (e.g., 's-1234567890abcdef0')
        replication_region: Current replication region

    Returns:
        Dictionary containing original topology information:
        - originalSourceRegion: AWS region where server was originally replicated from
        - originalAccountId: AWS account ID where replication was configured
        - originalReplicationConfigTemplateId: DRS replication config template ID
        - topologyLastUpdated: ISO timestamp when topology was last captured
        Returns None if server not found or topology not available

    Example:
        >>> topology = get_failback_topology('s-1234567890abcdef0', 'us-west-2')
        >>> if topology:
        ...     print(f"Original region: {topology['originalSourceRegion']}")
        ...     print(f"Original account: {topology['originalAccountId']}")
    """
    inventory_table = get_inventory_table()

    if not inventory_table:
        logger.warning("Inventory table not configured")
        return None

    try:
        # Get server record from inventory
        response = inventory_table.get_item(
            Key={"sourceServerID": source_server_id, "replicationRegion": replication_region}
        )

        server = response.get("Item")
        if not server:
            logger.warning(f"Server {source_server_id} not found in inventory database")
            return None

        # Check if topology information is available
        if not server.get("originalSourceRegion"):
            logger.warning(f"Server {source_server_id} missing original topology information (legacy server)")
            return None

        return {
            "originalSourceRegion": server.get("originalSourceRegion"),
            "originalAccountId": server.get("originalAccountId"),
            "originalReplicationConfigTemplateId": server.get("originalReplicationConfigTemplateId"),
            "topologyLastUpdated": server.get("topologyLastUpdated"),
        }

    except ClientError as e:
        logger.error(f"DynamoDB error retrieving failback topology: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error retrieving failback topology: {e}")
        return None


def _update_inventory_with_topology_preservation(server_data: Dict[str, Any], region: str) -> None:
    """
    Update inventory database while preserving original topology information.

    This helper function ensures that when inventory is updated (either during
    scheduled sync or fallback API queries), the original replication topology
    is preserved for failback operations.

    Topology Preservation Logic:
    - If server exists in inventory with topology: Preserve existing topology
    - If server is new: Capture current region/account as original topology
    - If server exists without topology: Add topology from current state

    Args:
        server_data: DRS source server data from API
        region: AWS region where server is replicated

    Example:
        >>> server = drs_client.describe_source_servers()[0]
        >>> _update_inventory_with_topology_preservation(server, 'us-east-1')
    """
    inventory_table = get_inventory_table()

    if not inventory_table:
        logger.warning("Inventory table not configured, skipping update")
        return

    try:
        source_server_id = server_data.get("sourceServerID")
        if not source_server_id:
            logger.warning("Server data missing sourceServerID, skipping update")
            return

        # Check if server already exists in inventory
        existing_response = inventory_table.get_item(
            Key={"sourceServerID": source_server_id, "replicationRegion": region}
        )

        existing_server = existing_response.get("Item")

        # Prepare updated server record
        updated_server = dict(server_data)
        updated_server["replicationRegion"] = region
        updated_server["lastUpdated"] = datetime.now(timezone.utc).isoformat()

        if existing_server and existing_server.get("originalSourceRegion"):
            # Preserve existing topology information
            updated_server["originalSourceRegion"] = existing_server["originalSourceRegion"]
            updated_server["originalAccountId"] = existing_server["originalAccountId"]
            updated_server["originalReplicationConfigTemplateId"] = existing_server.get(
                "originalReplicationConfigTemplateId"
            )
            updated_server["topologyLastUpdated"] = existing_server.get("topologyLastUpdated")
            logger.debug(f"Preserved existing topology for server {source_server_id}")
        else:
            # Capture current state as original topology (new server or legacy server)
            updated_server["originalSourceRegion"] = region
            updated_server["originalAccountId"] = (
                server_data.get("sourceProperties", {})
                .get("identificationHints", {})
                .get("awsInstanceID", "")
                .split(":")[4]
                if ":"
                in server_data.get("sourceProperties", {}).get("identificationHints", {}).get("awsInstanceID", "")
                else None
            )
            updated_server["originalReplicationConfigTemplateId"] = server_data.get(
                "replicationConfigurationTemplateID"
            )
            updated_server["topologyLastUpdated"] = datetime.now(timezone.utc).isoformat()
            logger.debug(f"Captured new topology for server {source_server_id}")

        # Write updated record to DynamoDB
        inventory_table.put_item(Item=updated_server)
        logger.debug(f"Updated inventory for server {source_server_id} in region {region}")

    except ClientError as e:
        logger.error(f"DynamoDB error updating inventory with topology preservation: {e}")
    except Exception as e:
        logger.error(f"Unexpected error updating inventory with topology preservation: {e}")


def _fallback_to_drs_api_and_update(
    regions: List[str], filters: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Fallback to DRS API when inventory is stale, then update inventory database.

    This function is called when inventory data is stale (older than 15 minutes).
    It queries the DRS API directly for fresh data, updates the inventory database
    with topology preservation, and returns the results.

    CRITICAL: This function preserves original replication topology for failback
    operations. When updating inventory, existing topology fields are preserved.

    Args:
        regions: List of AWS regions to query
        filters: Optional filters to apply (same as query_inventory_by_regions)

    Returns:
        List of server dictionaries in frontend-compatible format

    Example:
        >>> # Called automatically when inventory is stale
        >>> servers = _fallback_to_drs_api_and_update(['us-east-1', 'us-west-2'])
        >>> print(f"Retrieved and updated {len(servers)} servers")
    """
    logger.info(f"Falling back to DRS API for {len(regions)} regions and updating inventory")

    # Publish CloudWatch metric for inventory database miss
    publish_metric("InventoryDatabaseMisses", 1)

    all_servers = []

    for region in regions:
        try:
            drs_client = _get_drs_client(region)

            # Query DRS API for source servers
            logger.debug(f"Querying DRS API in region {region}")
            response = drs_client.describe_source_servers()

            servers = response.get("items", [])

            # Handle pagination
            while "nextToken" in response:
                response = drs_client.describe_source_servers(nextToken=response["nextToken"])
                servers.extend(response.get("items", []))

            logger.info(f"Retrieved {len(servers)} servers from DRS API in region {region}")

            # Update inventory database with topology preservation
            for server in servers:
                _update_inventory_with_topology_preservation(server, region)

            # Apply filters if specified
            if filters:
                servers = _apply_filters(servers, filters)

            all_servers.extend(servers)

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            if error_code == "UninitializedAccountException":
                logger.info(f"DRS not initialized in region {region}, skipping")
            else:
                logger.error(f"DRS API error in region {region}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error querying DRS API in region {region}: {e}")

    logger.info(f"Fallback complete: Retrieved {len(all_servers)} servers total, inventory updated")
    return all_servers


def _apply_filters(servers: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Apply filters to server list (used during DRS API fallback).

    Args:
        servers: List of server dictionaries
        filters: Filter criteria (same as query_inventory_by_regions)

    Returns:
        Filtered list of servers
    """
    filtered_servers = servers

    if "hostname" in filters:
        filtered_servers = [s for s in filtered_servers if s.get("hostname") == filters["hostname"]]

    if "replicationState" in filters:
        filtered_servers = [
            s
            for s in filtered_servers
            if s.get("dataReplicationInfo", {}).get("dataReplicationState") == filters["replicationState"]
        ]

    if "stagingAccountId" in filters:
        filtered_servers = [
            s
            for s in filtered_servers
            if s.get("stagingArea", {}).get("stagingAccountID") == filters["stagingAccountId"]
        ]

    if "sourceAccountId" in filters:
        filtered_servers = [
            s
            for s in filtered_servers
            if s.get("sourceProperties", {}).get("identificationHints", {}).get("awsInstanceID", "").split(":")[4]
            == filters["sourceAccountId"]
        ]

    if "minCpuCores" in filters:
        filtered_servers = [
            s
            for s in filtered_servers
            if s.get("sourceProperties", {}).get("cpus", [{}])[0].get("cores", 0) >= filters["minCpuCores"]
        ]

    if "minRamBytes" in filters:
        filtered_servers = [
            s for s in filtered_servers if s.get("sourceProperties", {}).get("ramBytes", 0) >= filters["minRamBytes"]
        ]

    return filtered_servers
