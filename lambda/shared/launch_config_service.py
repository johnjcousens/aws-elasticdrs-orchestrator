"""
Launch Configuration Service for Pre-Application and Status Management

This module provides core functionality for applying DRS launch configurations
to protection groups and managing configuration status in DynamoDB. It enables
the performance optimization of pre-applying configurations during group
operations rather than at runtime during wave execution.

Key Functions:
    - apply_launch_configs_to_group(): Apply configs to all servers in group
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
import time
from datetime import datetime, timezone
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
            raise LaunchConfigApplicationError("PROTECTION_GROUPS_TABLE environment variable not set")
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


def apply_launch_configs_to_group(
    group_id: str,
    region: str,
    server_ids: List[str],
    launch_configs: Dict[str, Dict],
    account_context: Optional[Dict] = None,
    timeout_seconds: int = 300,
    progress_callback: Optional[callable] = None,
) -> Dict:
    """
    Apply launch configurations to all servers in a protection group.

    Applies launch configurations to each server with timeout handling,
    retry logic, and per-server error tracking. Supports partial success
    where some servers succeed and others fail.

    Args:
        group_id: Protection group ID
        region: AWS region
        server_ids: List of DRS source server IDs
        launch_configs: Dict mapping server_id to launch config
        account_context: Cross-account context (for staging accounts)
        timeout_seconds: Maximum time to spend applying configs
        progress_callback: Optional callback function called with progress updates.
            Called every 10 servers or 30 seconds with dict containing:
            - completed: Number of servers processed
            - total: Total number of servers
            - percentage: Completion percentage (0-100)

    Returns:
        Dictionary containing application status with keys:
        - status: Overall status (ready | partial | failed)
        - appliedServers: Count of successfully applied servers
        - failedServers: Count of failed servers
        - serverConfigs: Per-server configuration status
        - errors: List of error messages

    Raises:
        LaunchConfigValidationError: When inputs are invalid
        LaunchConfigApplicationError: When DRS API fails critically

    Example:
        >>> result = apply_launch_configs_to_group(
        ...     group_id="pg-123",
        ...     region="us-east-2",
        ...     server_ids=["s-abc", "s-def"],
        ...     launch_configs={"s-abc": {...}, "s-def": {...}}
        ... )
        >>> result["status"]
        'ready'

    Validates: Requirements 1.1, 1.2, 1.4, 2.3, 2.7, 2.8, 4.6, 4.7, 4.8, 11.4
    """
    # Validate inputs
    if not group_id:
        raise LaunchConfigValidationError("group_id is required")
    if not region:
        raise LaunchConfigValidationError("region is required")
    if not server_ids:
        raise LaunchConfigValidationError("server_ids list cannot be empty")
    if not launch_configs:
        raise LaunchConfigValidationError("launch_configs dict cannot be empty")

    logger.info(
        f"Applying launch configs to group {group_id} with " f"{len(server_ids)} servers (timeout: {timeout_seconds}s)"
    )

    # Initialize result tracking
    start_time = time.time()
    applied_servers = 0
    failed_servers = 0
    server_configs = {}
    overall_errors = []

    # Progress tracking for callback
    total_servers = len(server_ids)
    completed_servers = 0
    last_callback_time = start_time

    # Helper function to call progress callback
    def _call_progress_callback():
        if progress_callback:
            try:
                percentage = (completed_servers / total_servers * 100) if total_servers > 0 else 0
                progress_callback(
                    {
                        "completed": completed_servers,
                        "total": total_servers,
                        "percentage": round(percentage, 2),
                    }
                )
            except Exception as e:
                logger.warning(f"Progress callback failed: {e}")

    # Get DRS client (with cross-account support if needed)
    try:
        if account_context:
            # Cross-account DRS client (for staging accounts)
            drs_client = _get_cross_account_drs_client(region, account_context)
        else:
            # Same-account DRS client
            drs_client = boto3.client("drs", region_name=region)
    except Exception as e:
        error_msg = f"Failed to create DRS client: {str(e)}"
        logger.error(error_msg)
        raise LaunchConfigApplicationError(error_msg)

    # Apply configuration to each server
    for idx, server_id in enumerate(server_ids):
        # Check timeout
        elapsed = time.time() - start_time
        if elapsed >= timeout_seconds:
            # Mark remaining servers as pending
            remaining_servers = server_ids[idx:]
            for remaining_id in remaining_servers:
                server_configs[remaining_id] = {
                    "status": "pending",
                    "lastApplied": None,
                    "configHash": None,
                    "errors": ["Configuration application timed out"],
                }
            overall_errors.append(
                f"Timeout after {elapsed:.1f}s, " f"{len(remaining_servers)} servers marked as pending"
            )
            logger.warning(f"Config application timeout for {group_id} after " f"{elapsed:.1f}s")
            break

        # Get launch config for this server
        launch_config = launch_configs.get(server_id)
        if not launch_config:
            # No config for this server - mark as failed
            server_configs[server_id] = {
                "status": "failed",
                "lastApplied": None,
                "configHash": None,
                "errors": [f"No launch config found for server {server_id}"],
            }
            failed_servers += 1
            completed_servers += 1
            continue

        # Apply configuration with exponential backoff retry logic
        max_retries = 3
        retry_delays = [1, 2, 4]  # Exponential backoff: 1s, 2s, 4s

        for attempt in range(max_retries):
            try:
                _apply_config_to_server(
                    drs_client,
                    server_id,
                    launch_config,
                    region,
                    account_context=account_context,
                )

                # Calculate config hash for drift detection
                config_hash = calculate_config_hash(launch_config)

                # Mark as ready
                server_configs[server_id] = {
                    "status": "ready",
                    "lastApplied": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "configHash": config_hash,
                    "errors": [],
                }
                applied_servers += 1

                logger.info(f"Successfully applied config to server {server_id}")
                break  # Success - exit retry loop

            except ClientError as e:
                # Handle boto3 ClientError with proper error code checking
                error_code = e.response.get("Error", {}).get("Code", "")
                error_msg = e.response.get("Error", {}).get("Message", str(e))
                is_throttling = error_code in ["ThrottlingException", "TooManyRequestsException"]

                # Retry on throttling errors
                if is_throttling and attempt < max_retries - 1:
                    delay = retry_delays[attempt]
                    logger.warning(
                        f"AWS API throttled for server {server_id}, "
                        f"retrying in {delay}s (attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(delay)
                    continue
                else:
                    # Final failure - no more retries
                    full_error_msg = f"{error_code}: {error_msg}"
                    if attempt == max_retries - 1:
                        full_error_msg = f"{full_error_msg} (failed after {max_retries} attempts)"

                    server_configs[server_id] = {
                        "status": "failed",
                        "lastApplied": None,
                        "configHash": None,
                        "errors": [full_error_msg],
                    }
                    failed_servers += 1
                    overall_errors.append(f"Server {server_id}: {full_error_msg}")

                    logger.error(f"Failed to apply config to server {server_id}: {full_error_msg}")
                    break  # Exit retry loop

            except Exception as e:
                # Handle other exceptions (LaunchConfigApplicationError, etc.)
                error_msg = str(e)
                is_throttling = "throttl" in error_msg.lower()

                # Retry on throttling errors
                if is_throttling and attempt < max_retries - 1:
                    delay = retry_delays[attempt]
                    logger.warning(
                        f"AWS API throttled for server {server_id}, "
                        f"retrying in {delay}s (attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(delay)
                    continue
                else:
                    # Final failure - no more retries
                    if attempt == max_retries - 1:
                        error_msg = f"{error_msg} (failed after {max_retries} attempts)"

                    server_configs[server_id] = {
                        "status": "failed",
                        "lastApplied": None,
                        "configHash": None,
                        "errors": [error_msg],
                    }
                    failed_servers += 1
                    overall_errors.append(f"Server {server_id}: {error_msg}")

                    logger.error(f"Failed to apply config to server {server_id}: {error_msg}")
                    break  # Exit retry loop

        # Update progress counter
        completed_servers += 1

        # Call progress callback every 10 servers or every 30 seconds
        time_since_last_callback = time.time() - last_callback_time
        if completed_servers % 10 == 0 or time_since_last_callback >= 30:
            _call_progress_callback()
            last_callback_time = time.time()

    # Final progress callback to ensure 100% is reported
    if progress_callback and completed_servers == total_servers:
        _call_progress_callback()

    # Determine overall status
    if applied_servers == len(server_ids):
        overall_status = "ready"
    elif applied_servers == 0:
        overall_status = "failed"
    else:
        overall_status = "partial"

    result = {
        "status": overall_status,
        "appliedServers": applied_servers,
        "failedServers": failed_servers,
        "serverConfigs": server_configs,
        "errors": overall_errors,
    }

    logger.info(
        f"Config application complete for {group_id}: "
        f"status={overall_status}, applied={applied_servers}, "
        f"failed={failed_servers}"
    )

    return result


def _apply_config_to_server(
    drs_client,
    server_id: str,
    launch_config: Dict,
    region: str,
    account_context: Optional[Dict] = None,
) -> None:
    """
    Apply launch configuration to a single server.

    Updates both DRS launch configuration and EC2 launch template.
    DRS update must happen FIRST to avoid being overwritten.

    Note: Retry logic is handled by the caller (apply_launch_configs_to_group).

    Args:
        drs_client: boto3 DRS client
        server_id: DRS source server ID
        launch_config: Launch configuration dictionary
        region: AWS region
        account_context: Cross-account context for EC2 client

    Raises:
        LaunchConfigApplicationError: When config application fails
    """
    # Prepare DRS API call parameters - only include DRS-specific fields
    # DRS update_launch_configuration accepts:
    # - copyPrivateIp, copyTags, launchDisposition, licensing
    # - targetInstanceTypeRightSizingMethod, postLaunchEnabled, name
    # EC2-specific fields (instanceType, subnetId, securityGroupIds, staticPrivateIp)
    # are NOT valid for DRS API and must be applied via EC2 launch template
    drs_update = {"sourceServerID": server_id}

    # If static IP is specified, disable copyPrivateIp to prevent DRS
    # from overriding it
    if launch_config.get("staticPrivateIp"):
        drs_update["copyPrivateIp"] = False
    elif "copyPrivateIp" in launch_config:
        drs_update["copyPrivateIp"] = launch_config["copyPrivateIp"]

    # Map other DRS-valid parameters
    drs_valid_params = [
        "copyTags",
        "launchDisposition",
        "licensing",
        "targetInstanceTypeRightSizingMethod",
        "postLaunchEnabled",
        "name",
    ]

    for param in drs_valid_params:
        if param in launch_config:
            drs_update[param] = launch_config[param]

    # STEP 1: Update DRS launch configuration FIRST
    # DRS creates new EC2 template versions, so we must call it before
    # our EC2 updates to avoid being overwritten
    try:
        if len(drs_update) > 1:  # More than just sourceServerID
            drs_client.update_launch_configuration(**drs_update)

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        error_msg = e.response.get("Error", {}).get("Message", "")

        # Handle validation errors
        if error_code == "ValidationException":
            raise LaunchConfigValidationError(f"Invalid launch config: {error_msg}")

        # Handle throttling - raise to allow caller to retry
        elif error_code in ["ThrottlingException", "TooManyRequestsException"]:
            raise LaunchConfigApplicationError(f"DRS API throttled: {error_msg}")

        # Handle other errors
        else:
            raise LaunchConfigApplicationError(f"DRS API error ({error_code}): {error_msg}")

    except Exception as e:
        # Unexpected error
        raise LaunchConfigApplicationError(f"Unexpected error applying DRS config: {str(e)}")

    # STEP 2: Update EC2 launch template (after DRS, so our changes stick)
    # Check if we have EC2-specific settings to apply
    has_ec2_settings = any(
        [
            launch_config.get("instanceType"),
            launch_config.get("subnetId"),
            launch_config.get("securityGroupIds"),
            launch_config.get("instanceProfileName"),
            launch_config.get("staticPrivateIp"),
        ]
    )

    if has_ec2_settings:
        try:
            # Get launch template ID from DRS configuration
            drs_config = drs_client.get_launch_configuration(sourceServerID=server_id)
            template_id = drs_config.get("ec2LaunchTemplateID")

            if not template_id:
                logger.warning(f"No EC2 launch template found for server {server_id}, skipping EC2 updates")
                return

            # Create EC2 client with same account context as DRS
            if account_context and not account_context.get("isCurrentAccount", True):
                from shared.cross_account import get_cross_account_session

                account_id = account_context["accountId"]
                assume_role_name = account_context.get("assumeRoleName")
                if assume_role_name:
                    role_arn = f"arn:aws:iam::{account_id}:role/{assume_role_name}"
                    external_id = account_context.get("externalId")
                    session = get_cross_account_session(role_arn, external_id)
                    ec2_client = session.client("ec2", region_name=region)
                    logger.info(f"Created cross-account EC2 client for account {account_id}")
                else:
                    ec2_client = boto3.client("ec2", region_name=region)
            else:
                ec2_client = boto3.client("ec2", region_name=region)

            # Build EC2 template data for the new version
            template_data = {}

            if launch_config.get("instanceType"):
                template_data["InstanceType"] = launch_config["instanceType"]

            # Network interface settings (subnet, security groups, static IP)
            if (
                launch_config.get("subnetId")
                or launch_config.get("securityGroupIds")
                or launch_config.get("staticPrivateIp")
            ):
                network_interface = {"DeviceIndex": 0}

                # Static private IP support
                if launch_config.get("staticPrivateIp"):
                    network_interface["PrivateIpAddress"] = launch_config["staticPrivateIp"]

                if launch_config.get("subnetId"):
                    network_interface["SubnetId"] = launch_config["subnetId"]
                if launch_config.get("securityGroupIds"):
                    network_interface["Groups"] = launch_config["securityGroupIds"]
                template_data["NetworkInterfaces"] = [network_interface]

            if launch_config.get("instanceProfileName"):
                template_data["IamInstanceProfile"] = {"Name": launch_config["instanceProfileName"]}

            # Create new launch template version with descriptive metadata
            version_desc = _build_version_description(launch_config, server_id)

            ec2_client.create_launch_template_version(
                LaunchTemplateId=template_id,
                LaunchTemplateData=template_data,
                VersionDescription=version_desc,
            )

            # Set new version as default
            ec2_client.modify_launch_template(LaunchTemplateId=template_id, DefaultVersion="$Latest")

            logger.info(f"Successfully updated EC2 launch template {template_id} for server {server_id}")

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            error_msg = e.response.get("Error", {}).get("Message", "")
            raise LaunchConfigApplicationError(f"EC2 API error ({error_code}): {error_msg}")

        except Exception as e:
            raise LaunchConfigApplicationError(f"Unexpected error updating EC2 template: {str(e)}")


def _build_version_description(launch_config: Dict, server_id: str) -> str:
    """
    Build descriptive version description for EC2 launch template.

    Args:
        launch_config: Launch configuration dictionary
        server_id: DRS source server ID

    Returns:
        Version description string (max 255 chars)
    """
    from datetime import datetime, timezone

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    desc_parts = [f"DRS Orchestration | {timestamp}"]

    # Add server ID (truncated)
    desc_parts.append(f"Server: {server_id[:12]}")

    # Add config details
    config_details = []
    if launch_config.get("staticPrivateIp"):
        config_details.append(f"IP:{launch_config['staticPrivateIp']}")
    if launch_config.get("instanceType"):
        config_details.append(f"Type:{launch_config['instanceType']}")
    if launch_config.get("subnetId"):
        config_details.append(f"Subnet:{launch_config['subnetId'][-8:]}")
    if launch_config.get("securityGroupIds"):
        sg_count = len(launch_config["securityGroupIds"])
        config_details.append(f"SGs:{sg_count}")
    if launch_config.get("instanceProfileName"):
        profile = launch_config["instanceProfileName"]
        if len(profile) > 20:
            profile = profile[:17] + "..."
        config_details.append(f"Profile:{profile}")
    if launch_config.get("copyPrivateIp"):
        config_details.append("CopyIP")
    if launch_config.get("copyTags"):
        config_details.append("CopyTags")
    if launch_config.get("targetInstanceTypeRightSizingMethod"):
        config_details.append(f"RightSize:{launch_config['targetInstanceTypeRightSizingMethod']}")
    if launch_config.get("launchDisposition"):
        config_details.append(f"Launch:{launch_config['launchDisposition']}")

    if config_details:
        desc_parts.append(" | ".join(config_details))

    # EC2 version description max 255 chars
    return " | ".join(desc_parts)[:255]


def _get_cross_account_drs_client(region: str, account_context: Dict):
    """
    Get DRS client for cross-account operations.

    Args:
        region: AWS region
        account_context: Dict with keys:
            - accountId: Target account ID
            - assumeRoleName: Role name to assume

    Returns:
        boto3 DRS client with assumed role credentials

    Raises:
        LaunchConfigApplicationError: When role assumption fails
    """
    try:
        sts_client = boto3.client("sts")

        # Assume role in target account
        role_arn = f"arn:aws:iam::{account_context['accountId']}:" f"role/{account_context['assumeRoleName']}"

        response = sts_client.assume_role(RoleArn=role_arn, RoleSessionName="launch-config-application")

        credentials = response["Credentials"]

        # Create DRS client with assumed role credentials
        drs_client = boto3.client(
            "drs",
            region_name=region,
            aws_access_key_id=credentials["AccessKeyId"],
            aws_secret_access_key=credentials["SecretAccessKey"],
            aws_session_token=credentials["SessionToken"],
        )

        return drs_client

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        error_msg = e.response.get("Error", {}).get("Message", "")
        raise LaunchConfigApplicationError(f"Failed to assume role ({error_code}): {error_msg}")


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


def persist_config_status(group_id: str, config_status: Dict, condition_expression: Optional[str] = None) -> None:
    """
    Persist configuration status to DynamoDB.

    Supports partial updates — only provided fields are updated.
    Uses conditional expressions for concurrency control.

    Args:
        group_id: Protection group ID
        config_status: Status dictionary with fields to update (partial updates supported):
            - status: Overall status (ready | pending | failed)
            - lastApplied: ISO timestamp
            - appliedBy: User identifier
            - serverConfigs: Per-server configuration status
            - errors: List of error messages
        condition_expression: Optional DynamoDB condition expression for concurrency control
            (e.g., "attribute_not_exists(launchConfigStatus.status) OR launchConfigStatus.status = :pending")

    Raises:
        LaunchConfigApplicationError: If DynamoDB update fails
        ConditionalCheckFailedException: If condition_expression fails (wrapped in LaunchConfigApplicationError)

    Example:
        >>> # Full update
        >>> status = {
        ...     "status": "ready",
        ...     "lastApplied": "2025-02-16T10:30:00Z",
        ...     "appliedBy": "user@example.com",
        ...     "serverConfigs": {},
        ...     "errors": []
        ... }
        >>> persist_config_status("pg-123", status)

        >>> # Partial update (only status field)
        >>> persist_config_status("pg-123", {"status": "pending"})

        >>> # Conditional update (only if status is pending)
        >>> persist_config_status(
        ...     "pg-123",
        ...     {"status": "ready"},
        ...     condition_expression="launchConfigStatus.#status = :pending"
        ... )

    Validates: Requirements 1.4, 8.4 (status persistence, partial updates, concurrency control)
    """
    if not group_id:
        raise LaunchConfigValidationError("group_id is required")

    if not config_status:
        raise LaunchConfigValidationError("config_status is required")

    try:
        table = _get_protection_groups_table()

        # Build UpdateExpression for partial updates
        update_parts = []
        expression_attribute_values = {}
        expression_attribute_names = {}

        for field_name, field_value in config_status.items():
            # Use attribute names to handle reserved words (like 'status')
            attr_name_placeholder = f"#{field_name}"
            attr_value_placeholder = f":{field_name}"

            update_parts.append(f"launchConfigStatus.{attr_name_placeholder} = {attr_value_placeholder}")
            expression_attribute_names[attr_name_placeholder] = field_name
            expression_attribute_values[attr_value_placeholder] = field_value

        update_expression = "SET " + ", ".join(update_parts)

        # Build update_item parameters
        update_params = {
            "Key": {"groupId": group_id},
            "UpdateExpression": update_expression,
            "ExpressionAttributeValues": expression_attribute_values,
            "ExpressionAttributeNames": expression_attribute_names,
        }

        # Add condition expression if provided
        if condition_expression:
            update_params["ConditionExpression"] = condition_expression

        # Execute update
        table.update_item(**update_params)

        logger.info(
            f"Persisted config status for group {group_id}: "
            f"fields={list(config_status.keys())}, "
            f"conditional={condition_expression is not None}"
        )

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        error_message = e.response["Error"]["Message"]

        # Handle conditional check failure specifically
        if error_code == "ConditionalCheckFailedException":
            logger.warning(
                f"Conditional check failed for {group_id}: {error_message} " f"(condition: {condition_expression})"
            )
            raise LaunchConfigApplicationError(
                f"Conditional update failed: {error_message} (condition: {condition_expression})"
            )

        logger.error(f"Failed to persist config status for {group_id}: " f"{error_code} - {error_message}")
        raise LaunchConfigApplicationError(f"DynamoDB update failed: {error_code}")


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
            raise LaunchConfigApplicationError(f"Protection group {group_id} not found")

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
        logger.error(f"Failed to get config status for {group_id}: " f"{error_code} - {error_message}")
        raise LaunchConfigApplicationError(f"DynamoDB query failed: {error_code}")


def detect_config_drift(group_id: str, current_configs: Dict[str, Dict]) -> Dict:
    """
    Detect configuration drift by comparing current config hashes
    with stored hashes.

    Configuration drift occurs when the current launch configurations
    differ from the configurations that were previously applied and
    stored in DynamoDB. This function calculates hashes for current
    configurations and compares them with stored hashes to identify
    which servers have drifted.

    Args:
        group_id: Protection group ID
        current_configs: Current launch configurations mapping
            server_id to launch config dict

    Returns:
        Dictionary containing drift detection results with keys:
        - hasDrift: Boolean indicating if any drift detected
        - driftedServers: List of server IDs with configuration drift
        - details: Dict mapping server_id to drift details with keys:
            - currentHash: Hash of current configuration
            - storedHash: Hash of stored configuration
            - reason: Explanation of drift

    Example:
        >>> current = {"s-abc": {"instanceType": "t3.large"}}
        >>> result = detect_config_drift("pg-123", current)
        >>> result["hasDrift"]
        False

    Validates: Requirements 4.4 (drift detection)
    """
    if not group_id:
        raise LaunchConfigValidationError("group_id is required")

    if current_configs is None:
        current_configs = {}

    logger.info(f"Detecting config drift for group {group_id} with " f"{len(current_configs)} current configs")

    # Get stored configuration status
    try:
        stored_status = get_config_status(group_id)
    except LaunchConfigApplicationError as e:
        # If we can't get stored status, treat as drift
        logger.warning(f"Failed to get stored config status for {group_id}: {e}")
        return {
            "hasDrift": True,
            "driftedServers": list(current_configs.keys()),
            "details": {
                server_id: {
                    "currentHash": calculate_config_hash(config),
                    "storedHash": None,
                    "reason": "Unable to retrieve stored configuration status",
                }
                for server_id, config in current_configs.items()
            },
        }

    # If no stored status, treat as drift
    if stored_status["status"] == "not_configured":
        logger.info(f"No stored config status for {group_id}, treating as drift")
        return {
            "hasDrift": True,
            "driftedServers": list(current_configs.keys()),
            "details": {
                server_id: {
                    "currentHash": calculate_config_hash(config),
                    "storedHash": None,
                    "reason": "No stored configuration status",
                }
                for server_id, config in current_configs.items()
            },
        }

    # Compare hashes for each server
    drifted_servers = []
    drift_details = {}
    stored_server_configs = stored_status.get("serverConfigs", {})

    # Handle empty current configs (no drift if no configs to check)
    if not current_configs:
        logger.info(f"No current configs provided for {group_id}, no drift detected")
        return {"hasDrift": False, "driftedServers": [], "details": {}}

    for server_id, current_config in current_configs.items():
        # Calculate current config hash
        current_hash = calculate_config_hash(current_config)

        # Get stored config for this server
        stored_config = stored_server_configs.get(server_id)

        if not stored_config:
            # No stored config for this server - treat as drift
            drifted_servers.append(server_id)
            drift_details[server_id] = {
                "currentHash": current_hash,
                "storedHash": None,
                "reason": "No stored configuration for this server",
            }
            logger.info(f"Drift detected for {server_id}: no stored configuration")
            continue

        # Get stored hash
        stored_hash = stored_config.get("configHash")

        if not stored_hash:
            # Stored config exists but no hash - treat as drift
            drifted_servers.append(server_id)
            drift_details[server_id] = {
                "currentHash": current_hash,
                "storedHash": None,
                "reason": "Stored configuration has no hash",
            }
            logger.info(f"Drift detected for {server_id}: stored config has no hash")
            continue

        # Compare hashes
        if current_hash != stored_hash:
            # Hash mismatch - configuration has drifted
            drifted_servers.append(server_id)
            drift_details[server_id] = {
                "currentHash": current_hash,
                "storedHash": stored_hash,
                "reason": "Configuration hash mismatch",
            }
            logger.info(
                f"Drift detected for {server_id}: hash mismatch "
                f"(current={current_hash[:16]}..., "
                f"stored={stored_hash[:16]}...)"
            )

    has_drift = len(drifted_servers) > 0

    result = {
        "hasDrift": has_drift,
        "driftedServers": drifted_servers,
        "details": drift_details,
    }

    logger.info(
        f"Drift detection complete for {group_id}: " f"hasDrift={has_drift}, driftedServers={len(drifted_servers)}"
    )

    return result
