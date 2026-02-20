"""
Active Region Filtering Module

Provides region filtering functionality to optimize DRS multi-region operations.
Queries the DRSRegionStatusTable to identify regions with active DRS servers,
reducing API calls by 80-90% for typical deployments.

Key Functions:
- get_active_regions(): Get list of active regions
- update_region_status(): Update region status in DynamoDB
- invalidate_region_cache(): Clear cached region data

Usage:
    from shared.active_region_filter import get_active_regions

    active_regions = get_active_regions()
    for region in active_regions:
        scan_region(region)
"""

import logging
import os
import time
from typing import Dict, List, Optional

import boto3
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError

from shared.drs_regions import DRS_REGIONS

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Environment variables
DRS_REGION_STATUS_TABLE = os.environ.get("DRS_REGION_STATUS_TABLE")

# DynamoDB client (lazy initialization)
dynamodb = boto3.resource("dynamodb")
_region_status_table = None

# CloudWatch client (lazy initialization)
cloudwatch = boto3.client("cloudwatch")

# Cache for active regions (prevents repeated DynamoDB queries)
_region_cache: Dict[str, any] = {}
CACHE_TTL = 60  # Cache time-to-live in seconds


def get_region_status_table():
    """
    Get or initialize region status table.

    Returns:
        DynamoDB Table resource or None if not configured
    """
    global _region_status_table
    if _region_status_table is None:
        if DRS_REGION_STATUS_TABLE:
            _region_status_table = dynamodb.Table(DRS_REGION_STATUS_TABLE)
        else:
            logger.warning("DRS_REGION_STATUS_TABLE environment variable not set")
    return _region_status_table


def publish_metric(metric_name: str, value: float, unit: str = "Count") -> None:
    """
    Publish custom CloudWatch metric for active region filtering.

    Publishes metrics to the DRSOrchestration/ActiveRegionFiltering namespace
    for monitoring region filtering effectiveness and performance.

    Args:
        metric_name: Name of the metric (e.g., 'ActiveRegionCount')
        value: Metric value to publish
        unit: CloudWatch unit (default: 'Count')

    Example:
        >>> publish_metric('ActiveRegionCount', 3)
        >>> publish_metric('RegionsSkipped', 25)
    """
    try:
        cloudwatch.put_metric_data(
            Namespace="DRSOrchestration/ActiveRegionFiltering",
            MetricData=[{"MetricName": metric_name, "Value": value, "Unit": unit}],
        )
        logger.debug(f"Published CloudWatch metric: {metric_name}={value} {unit}")
    except Exception as e:
        logger.warning(f"Failed to publish CloudWatch metric {metric_name}: {e}")


def _is_cache_valid(cache_ttl: int) -> bool:
    """
    Check if cached region data is still valid.

    Cache prevents DynamoDB throttling during concurrent operations
    like tag sync which may call get_active_regions multiple times.

    Args:
        cache_ttl: Cache time-to-live in seconds

    Returns:
        True if cache exists and is within TTL window
    """
    if "active_regions" not in _region_cache:
        return False

    cached_data = _region_cache["active_regions"]
    age = time.time() - cached_data["timestamp"]

    if age > cache_ttl:
        logger.debug(f"Cache expired (age: {age:.1f}s, TTL: {cache_ttl}s)")
        return False

    logger.debug(f"Cache valid (age: {age:.1f}s, TTL: {cache_ttl}s)")
    return True


def get_active_regions(region_status_table=None, cache_ttl: int = CACHE_TTL) -> List[str]:
    """
    Get list of active DRS regions (regions with serverCount > 0).

    Queries the DRSRegionStatusTable to identify regions with active DRS servers.
    Uses caching to avoid repeated DynamoDB queries within TTL window.
    Falls back to all DRS_REGIONS if table is empty or unavailable.

    Args:
        region_status_table: DynamoDB table resource (optional, uses env var if None)
        cache_ttl: Cache time-to-live in seconds (default: 60)

    Returns:
        List of active region names (e.g., ['us-east-1', 'us-west-2'])

    Example:
        >>> active_regions = get_active_regions()
        >>> print(f"Scanning {len(active_regions)} regions")
        Scanning 3 regions
    """
    # Check cache first to avoid repeated DynamoDB queries
    if _is_cache_valid(cache_ttl):
        cached_regions = _region_cache["active_regions"]["data"]
        logger.debug(f"Returning {len(cached_regions)} active regions from cache")
        return cached_regions

    # Get table reference
    if region_status_table is None:
        region_status_table = get_region_status_table()

    # Fallback to all regions if table not configured
    if not region_status_table:
        logger.warning("Region status table not configured, falling back to all DRS regions")
        return DRS_REGIONS

    try:
        # Query DynamoDB for region statuses
        logger.debug("Querying region status table for active regions")
        result = region_status_table.scan(FilterExpression=Attr("serverCount").gt(0))

        active_regions = [item["region"] for item in result.get("Items", [])]

        # Handle pagination (table should have max 28 regions, but handle anyway)
        while "LastEvaluatedKey" in result:
            result = region_status_table.scan(
                FilterExpression=Attr("serverCount").gt(0),
                ExclusiveStartKey=result["LastEvaluatedKey"],
            )
            active_regions.extend([item["region"] for item in result.get("Items", [])])

        # Fallback to all regions if table is empty (new deployments)
        if not active_regions:
            logger.warning("Region status table empty, falling back to all DRS regions")
            return DRS_REGIONS

        # Cache the results
        _region_cache["active_regions"] = {
            "data": active_regions,
            "timestamp": time.time(),
        }

        logger.info(
            f"Found {len(active_regions)} active regions "
            f"(skipping {len(DRS_REGIONS) - len(active_regions)} inactive)"
        )

        # Publish CloudWatch metrics for monitoring
        publish_metric("ActiveRegionCount", len(active_regions))
        publish_metric("RegionsSkipped", len(DRS_REGIONS) - len(active_regions))

        return active_regions

    except ClientError as e:
        logger.error(f"DynamoDB error querying region status table: {e}")
        logger.warning("Falling back to all DRS regions")
        return DRS_REGIONS
    except Exception as e:
        logger.error(f"Unexpected error querying region status table: {e}")
        logger.warning("Falling back to all DRS regions")
        return DRS_REGIONS


def invalidate_region_cache() -> None:
    """
    Invalidate the region status cache.

    Should be called after source server inventory sync completes
    to ensure fresh data on next query.

    Example:
        >>> invalidate_region_cache()
        >>> # Next call to get_active_regions() will query DynamoDB
    """
    if "active_regions" in _region_cache:
        logger.debug("Invalidating region status cache")
        _region_cache.clear()
    else:
        logger.debug("Region cache already empty")


def update_region_status(region: str, server_count: int, error_message: Optional[str] = None) -> None:
    """
    Update region status in DynamoDB table.

    Called by inventory sync to maintain accurate region status.
    Updates serverCount and lastChecked timestamp for the region.

    Args:
        region: AWS region name (e.g., 'us-east-1')
        server_count: Number of DRS source servers in region
        error_message: Optional error message if region scan failed

    Example:
        >>> update_region_status('us-east-1', 42)
        >>> update_region_status('us-west-2', 0, error_message='DRS not initialized')
    """
    region_status_table = get_region_status_table()

    if not region_status_table:
        logger.warning("Region status table not configured, skipping status update")
        return

    try:
        # Determine status based on server count and error
        if error_message:
            status = "ERROR"
        elif server_count > 0:
            status = "AVAILABLE"
        else:
            status = "UNINITIALIZED"

        # Prepare item for DynamoDB
        item = {
            "region": region,
            "status": status,
            "serverCount": server_count,
            "lastChecked": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

        if error_message:
            item["errorMessage"] = error_message
        else:
            # Remove errorMessage if previously set
            item["errorMessage"] = None

        # Update DynamoDB
        region_status_table.put_item(Item=item)

        logger.debug(f"Updated region status: {region} - " f"status={status}, serverCount={server_count}")

    except ClientError as e:
        logger.error(f"DynamoDB error updating region status for {region}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error updating region status for {region}: {e}")
