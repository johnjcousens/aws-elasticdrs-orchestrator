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


def query_inventory_by_regions(regions: List[str], filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Query source server inventory database for specified regions.

    Provides fast access to server data without DRS API calls.
    Falls back to empty list if inventory is stale or unavailable
    (caller should handle fallback to DRS API).

    Args:
        regions: List of AWS regions to query (e.g., ['us-east-1', 'us-west-2'])
        filters: Optional filters to apply:
            - hostname: Filter by hostname (exact match)
            - replicationState: Filter by replication state (e.g., 'CONTINUOUS')
            - stagingAccountId: Filter by staging account ID
            - sourceAccountId: Filter by source account ID
            - minCpuCores: Minimum CPU cores
            - minRamBytes: Minimum RAM in bytes

    Returns:
        List of server dictionaries in frontend-compatible format.
        Returns empty list if inventory is unavailable or stale.

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

        logger.info(f"Retrieved {len(servers)} servers from inventory database " f"for {len(regions)} regions")

        return servers

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
