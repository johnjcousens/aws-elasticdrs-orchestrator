"""
Launch Configuration Service for Pre-Application and Status Management

This module provides core functionality for applying DRS launch configurations
to protection groups and managing configuration status in DynamoDB. It enables
the performance optimization of pre-applying configurations during group
operations rather than at runtime during wave execution.

Key Functions:
    - calculate_config_hash(): Calculate SHA-256 hash for drift detection
    - persist_config_status(): Store configuration status in DynamoDB
    - get_config_status(): Retrieve configuration status from DynamoDB

Error Classes:
    - LaunchConfigApplicationError: Base exception for config errors
    - LaunchConfigTimeoutError: Configuration application timeout
    - LaunchConfigValidationError: Configuration validation failure

Validates: Requirements 1.1, 1.2, 1.3, 1.4
"""

import hashlib
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# DynamoDB resource (lazy initialization)
_dynamodb = None
_protection_groups_table = None


def _get_dynamodb_resource():
    """Get or create DynamoDB resource."""
    global _dynamodb
    if _dynamodb is None:
        _dynamodb = boto3.resource("dynamodb")
    return _dynamodb


def _get_protection_groups_table():
    """Get or create protection groups table reference."""
    global _protection_groups_table
    if _protection_groups_table is None:
        table_name = os.environ.get("PROTECTION_GROUPS_TABLE")
        if not table_name:
            raise LaunchConfigApplicationError(
                "PROTECTION_GROUPS_TABLE environment variable not set"
            )
        dynamodb = _get_dynamodb_resource()
        _protection_groups_table = dynamodb.Table(table_name)
    return _protection_groups_table


class LaunchConfigApplicationError(Exception):
    """Base exception for launch config application errors."""

    pass


class LaunchConfigTimeoutError(LaunchConfigApplicationError):
    """Raised when config application exceeds timeout."""

    pass


class LaunchConfigValidationError(LaunchConfigApplicationError):
    """Raised when config validation fails."""

    pass


def calculate_config_hash(launch_config: Dict) -> str:
    """
    Calculate SHA-256 hash of launch configuration for drift detection.

    Hash calculation must be deterministic to enable reliable drift detection.
    Keys are sorted to ensure consistent ordering regardless of insertion order.

    Args:
        launch_config: Launch configuration dictionary

    Returns:
        Hash string in format "sha256:abc123..."

    Example:
        >>> config = {"instanceType": "t3.medium", "copyPrivateIp": True}
        >>> hash1 = calculate_config_hash(config)
        >>> hash2 = calculate_config_hash(config)
        >>> hash1 == hash2
        True

    Validates: Requirements 4.4 (drift detection)
    """
    if not launch_config:
        return "sha256:empty"

    # Sort keys to ensure consistent ordering for hash calculation
    sorted_config = json.dumps(launch_config, sort_keys=True)
    hash_bytes = hashlib.sha256(sorted_config.encode()).hexdigest()
    return f"sha256:{hash_bytes}"


def persist_config_status(group_id: str, config_status: Dict) -> None:
    """
    Persist configuration status to DynamoDB.

    Updates the launchConfigStatus field in the protection group item.
    Uses atomic update to ensure consistency.

    Args:
        group_id: Protection group ID
        config_status: Status dictionary to persist with keys:
            - status: Overall status (ready | pending | failed)
            - lastApplied: ISO timestamp
            - appliedBy: User identifier
            - serverConfigs: Per-server configuration status
            - errors: List of error messages

    Raises:
        LaunchConfigApplicationError: If DynamoDB update fails

    Example:
        >>> status = {
        ...     "status": "ready",
        ...     "lastApplied": "2025-02-16T10:30:00Z",
        ...     "appliedBy": "user@example.com",
        ...     "serverConfigs": {},
        ...     "errors": []
        ... }
        >>> persist_config_status("pg-123", status)

    Validates: Requirements 1.4 (status persistence)
    """
    if not group_id:
        raise LaunchConfigValidationError("group_id is required")

    if not config_status:
        raise LaunchConfigValidationError("config_status is required")

    # Validate required fields
    required_fields = ["status", "serverConfigs", "errors"]
    for field in required_fields:
        if field not in config_status:
            raise LaunchConfigValidationError(
                f"config_status missing required field: {field}"
            )

    try:
        table = _get_protection_groups_table()

        # Update protection group with configuration status
        table.update_item(
            Key={"groupId": group_id},
            UpdateExpression="SET launchConfigStatus = :status",
            ExpressionAttributeValues={":status": config_status},
        )

        logger.info(
            f"Persisted config status for group {group_id}: "
            f"status={config_status['status']}"
        )

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]
        logger.error(
            f"Failed to persist config status for {group_id}: "
            f"{error_code} - {error_message}"
        )
        raise LaunchConfigApplicationError(
            f"DynamoDB update failed: {error_code}"
        )


def get_config_status(group_id: str) -> Dict:
    """
    Retrieve configuration status from DynamoDB.

    Args:
        group_id: Protection group ID

    Returns:
        Configuration status dictionary with keys:
        - status: Overall status (ready | pending | failed | not_configured)
        - lastApplied: ISO timestamp (optional)
        - appliedBy: User identifier (optional)
        - serverConfigs: Per-server configuration status
        - errors: List of error messages

        If no status exists, returns default not_configured status.

    Raises:
        LaunchConfigApplicationError: If DynamoDB query fails

    Example:
        >>> status = get_config_status("pg-123")
        >>> status["status"]
        'ready'

    Validates: Requirements 2.1, 2.2 (status retrieval)
    """
    if not group_id:
        raise LaunchConfigValidationError("group_id is required")

    try:
        table = _get_protection_groups_table()

        response = table.get_item(Key={"groupId": group_id})

        if "Item" not in response:
            logger.warning(f"Protection group {group_id} not found")
            raise LaunchConfigApplicationError(
                f"Protection group {group_id} not found"
            )

        item = response["Item"]

        # Return launchConfigStatus if it exists, otherwise default status
        if "launchConfigStatus" in item:
            return item["launchConfigStatus"]
        else:
            # Default status for groups without configuration status
            return {
                "status": "not_configured",
                "lastApplied": None,
                "appliedBy": None,
                "serverConfigs": {},
                "errors": [],
            }

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]
        logger.error(
            f"Failed to get config status for {group_id}: "
            f"{error_code} - {error_message}"
        )
        raise LaunchConfigApplicationError(
            f"DynamoDB query failed: {error_code}"
        )
