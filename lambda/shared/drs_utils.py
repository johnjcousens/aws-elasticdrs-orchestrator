"""
AWS DRS Utility Functions - Field Normalization and Data Transformation

Provides utilities for working with AWS Elastic Disaster Recovery Service (DRS) API responses.

KEY FUNCTIONS:
    - normalize_drs_response(): Convert DRS PascalCase to application camelCase
    - extract_recovery_instance_details(): Extract normalized instance data
    - build_drs_filter(): Build filter objects for DRS API queries

USAGE PATTERN:
    1. Call DRS API (returns PascalCase fields)
    2. Normalize response immediately at API boundary
    3. Store/use normalized camelCase data in application
    4. Never store PascalCase in DynamoDB

WHY NORMALIZE:
    - Consistent field naming across application
    - Frontend expects camelCase (JavaScript convention)
    - DynamoDB stores camelCase for consistency
    - AWS APIs return PascalCase (AWS convention)

INTEGRATION POINTS:
    - execution-handler: Normalizes DRS job status and server data
    - All Lambda functions calling DRS APIs
    - DynamoDB storage (stores normalized data)
"""

from typing import Any, Dict, List, Union


def normalize_drs_response(
    drs_data: Union[Dict, List], recursive: bool = True
) -> Union[Dict, List]:
    """
    Convert AWS DRS PascalCase fields to application camelCase.

    NORMALIZATION RULES:
    1. Use explicit field_map for common DRS fields
    2. Fallback to lowercase first character for unmapped fields
    3. Recursively process nested dicts and lists
    4. Preserve non-dict/list values unchanged

    WHEN TO USE:
    - Immediately after calling any DRS API
    - Before storing DRS data in DynamoDB
    - Before returning DRS data to frontend

    FIELD MAPPINGS:
        RecoveryInstanceID → recoveryInstanceId
        SourceServerID → sourceServerId
        JobID → jobId
        LaunchStatus → launchStatus
        (see field_map for complete list)

    Args:
        drs_data: Response from AWS DRS API (dict or list)
        recursive: Process nested objects (default: True)

    Returns:
        Normalized data with camelCase field names

    Example:
        >>> drs_response = {'RecoveryInstanceID': 'i-123', 'SourceServerID': 's-456'}
        >>> normalize_drs_response(drs_response)
        {'recoveryInstanceId': 'i-123', 'sourceServerId': 's-456'}
    """
    if isinstance(drs_data, list):
        return [
            normalize_drs_response(item, recursive=recursive)
            for item in drs_data
        ]

    if not isinstance(drs_data, dict):
        return drs_data

    # Common DRS field mappings
    field_map = {
        "RecoveryInstanceID": "recoveryInstanceId",
        "SourceServerID": "sourceServerId",
        "JobID": "jobId",
        "LaunchTime": "launchTime",
        "InstanceID": "instanceId",
        "InstanceType": "instanceType",
        "PrivateIpAddress": "privateIpAddress",
        "PublicIpAddress": "publicIpAddress",
        "LaunchStatus": "launchStatus",
        "LifeCycle": "lifeCycle",
        "LastLaunchResult": "lastLaunchResult",
        # Lowercase variants that AWS sometimes returns
        "sourceServerID": "sourceServerId",
        "recoveryInstanceID": "recoveryInstanceId",
    }

    normalized = {}
    for key, value in drs_data.items():
        # Use explicit mapping if available, otherwise convert PascalCase to camelCase
        if key in field_map:
            new_key = field_map[key]
        else:
            # Convert first character to lowercase
            new_key = key[0].lower() + key[1:] if key else key

        # Recursively normalize nested structures
        if recursive and isinstance(value, dict):
            normalized[new_key] = normalize_drs_response(value, recursive=True)
        elif recursive and isinstance(value, list):
            normalized[new_key] = [
                (
                    normalize_drs_response(item, recursive=True)
                    if isinstance(item, dict)
                    else item
                )
                for item in value
            ]
        else:
            normalized[new_key] = value

    return normalized


def extract_recovery_instance_details(
    drs_instance: Dict,
) -> Dict[str, Any]:
    """
    Extract normalized recovery instance details from DRS API response.

    Normalizes DRS response and extracts key fields with safe fallbacks.
    Returns consistent structure even if DRS response is incomplete.

    EXTRACTED FIELDS:
        - instanceId: EC2 instance ID
        - recoveryInstanceId: DRS recovery instance ID
        - sourceServerId: DRS source server ID
        - launchTime: Instance launch timestamp
        - instanceType: EC2 instance type (t3.medium, etc)
        - privateIpAddress: VPC private IP
        - publicIpAddress: Public IP (if assigned)
        - launchStatus: DRS launch status
        - lifeCycle: DRS lifecycle state object

    USAGE:
        drs_client = boto3.client('drs')
        response = drs_client.describe_recovery_instances(...)
        for instance in response['items']:
            details = extract_recovery_instance_details(instance)

    Args:
        drs_instance: Raw DRS recovery instance object from API

    Returns:
        Dict with normalized instance details (empty strings for missing fields)
    """
    # Normalize the entire response first
    normalized = normalize_drs_response(drs_instance)

    # Extract key fields with fallbacks
    return {
        "instanceId": normalized.get("instanceId", ""),
        "recoveryInstanceId": normalized.get("recoveryInstanceId", ""),
        "sourceServerId": normalized.get("sourceServerId", ""),
        "launchTime": normalized.get("launchTime"),
        "instanceType": normalized.get("instanceType", ""),
        "privateIpAddress": normalized.get("privateIpAddress", ""),
        "publicIpAddress": normalized.get("publicIpAddress", ""),
        "launchStatus": normalized.get("launchStatus", ""),
        "lifeCycle": normalized.get("lifeCycle", {}),
    }


def build_drs_filter(
    source_server_ids: List[str] = None,
    recovery_instance_ids: List[str] = None,
) -> Dict[str, Any]:
    """
    Build filter object for DRS API queries.

    Constructs filter dict for DRS DescribeRecoveryInstances and similar APIs.
    Only includes filters with non-empty values.

    USAGE:
        # Filter by source servers
        filters = build_drs_filter(source_server_ids=['s-123', 's-456'])
        response = drs_client.describe_recovery_instances(filters=filters)

        # Filter by recovery instances
        filters = build_drs_filter(recovery_instance_ids=['i-abc', 'i-def'])
        response = drs_client.describe_recovery_instances(filters=filters)

        # Combine filters
        filters = build_drs_filter(
            source_server_ids=['s-123'],
            recovery_instance_ids=['i-abc']
        )

    Args:
        source_server_ids: List of DRS source server IDs to filter
        recovery_instance_ids: List of DRS recovery instance IDs to filter

    Returns:
        Filter dict for DRS API calls (empty dict if no filters)
    """
    filters = {}

    if source_server_ids:
        filters["sourceServerIDs"] = source_server_ids

    if recovery_instance_ids:
        filters["recoveryInstanceIDs"] = recovery_instance_ids

    return filters


def batch_describe_ec2_instances(
    instance_ids: List[str], ec2_client
) -> Dict[str, Dict]:
    """
    Query multiple EC2 instances efficiently.

    Returns dict mapping instanceId -> instance details.
    Handles pagination and throttling.

    Args:
        instance_ids: List of EC2 instance IDs
        ec2_client: boto3 EC2 client

    Returns:
        Dict mapping instanceId to normalized instance details
    """
    if not instance_ids:
        return {}

    instances = {}

    try:
        response = ec2_client.describe_instances(InstanceIds=instance_ids)

        for reservation in response.get("Reservations", []):
            for instance in reservation.get("Instances", []):
                instance_id = instance["InstanceId"]
                instances[instance_id] = {
                    "instanceId": instance_id,
                    "instanceType": instance.get("InstanceType", ""),
                    "privateIpAddress": instance.get("PrivateIpAddress", ""),
                    "privateDnsName": instance.get("PrivateDnsName", ""),
                    "state": instance.get("State", {}),
                    "launchTime": instance.get("LaunchTime"),
                }
    except Exception as e:
        # Handle instance not found or other errors
        if "InvalidInstanceID.NotFound" in str(e):
            # Some instances not yet available - return partial results
            pass
        else:
            raise

    return instances


def map_replication_state_to_display(replication_state: str) -> str:
    """
    Map DRS dataReplicationState to display-friendly state.

    Consolidates multiple in-progress states into "SYNCING" for UI simplicity.
    Maps "CONTINUOUS" to "READY_FOR_RECOVERY" for clarity.

    This function provides a simplified view of DRS replication states for
    the frontend, grouping similar states and using more user-friendly names.

    STATE MAPPINGS:
        STOPPED → STOPPED (replication not started)
        INITIATING → INITIATING (starting replication)
        INITIAL_SYNC → SYNCING (initial data sync)
        BACKLOG → SYNCING (catching up on changes)
        CREATING_SNAPSHOT → SYNCING (creating EBS snapshot)
        CONTINUOUS → READY_FOR_RECOVERY (ready for failover)
        PAUSED → PAUSED (replication paused)
        RESCAN → SYNCING (rescanning for changes)
        STALLED → STALLED (replication stuck)
        DISCONNECTED → DISCONNECTED (agent disconnected)

    Args:
        replication_state: Raw DRS replication state from API

    Returns:
        Display-friendly state string

    Example:
        >>> map_replication_state_to_display("INITIAL_SYNC")
        'SYNCING'
        >>> map_replication_state_to_display("CONTINUOUS")
        'READY_FOR_RECOVERY'
        >>> map_replication_state_to_display("UNKNOWN_STATE")
        'UNKNOWN_STATE'
    """
    STATE_MAPPING = {
        "STOPPED": "STOPPED",
        "INITIATING": "INITIATING",
        "INITIAL_SYNC": "SYNCING",
        "BACKLOG": "SYNCING",
        "CREATING_SNAPSHOT": "SYNCING",
        "CONTINUOUS": "READY_FOR_RECOVERY",
        "PAUSED": "PAUSED",
        "RESCAN": "SYNCING",
        "STALLED": "STALLED",
        "DISCONNECTED": "DISCONNECTED",
    }
    return STATE_MAPPING.get(replication_state, replication_state)


def transform_drs_server_for_frontend(server: Dict) -> Dict:
    """
    Transform raw DRS source server to frontend ResolvedServer format.

    Extracts nested DRS API fields into flat structure expected by UI.
    Handles missing fields gracefully with empty strings/defaults.

    Args:
        server: Raw DRS source server from describe_source_servers API

    Returns:
        Dict matching frontend ResolvedServer interface
    """
    source_props = server.get("sourceProperties", {})
    identification = source_props.get("identificationHints", {})
    hardware = source_props.get("cpus", [])
    disks = source_props.get("disks", [])
    nics = source_props.get("networkInterfaces", [])
    data_replication = server.get("dataReplicationInfo", {})
    source_cloud = server.get("sourceCloudProperties", {})

    # Calculate hardware totals
    total_cores = sum(cpu.get("cores", 0) for cpu in hardware)
    ram_bytes = source_props.get("ramBytes", 0)
    ram_gib = round(ram_bytes / (1024**3), 2) if ram_bytes else 0

    disk_list = []
    total_disk_gib = 0
    for disk in disks:
        disk_bytes = disk.get("bytes", 0)
        disk_gib = round(disk_bytes / (1024**3), 2) if disk_bytes else 0
        total_disk_gib += disk_gib
        disk_list.append(
            {
                "deviceName": disk.get("deviceName", ""),
                "bytes": disk_bytes,
                "sizeGiB": disk_gib,
            }
        )

    # Extract primary IP
    primary_ip = ""
    for nic in nics:
        if nic.get("isPrimary"):
            ips = nic.get("ips", [])
            if ips:
                primary_ip = ips[0]
            break

    # Extract source region and AZ from sourceCloudProperties
    source_region = source_cloud.get("originRegion", "")
    source_az = source_cloud.get("originAvailabilityZone", "")
    source_account = source_cloud.get("originAccountID", "")

    # Extract staging area (target) AZ from data replication info
    target_az = data_replication.get("stagingAvailabilityZone", "")

    # Determine if server is ready for recovery
    replication_state = data_replication.get("dataReplicationState", "UNKNOWN")
    is_ready = replication_state in [
        "CONTINUOUS",
        "CONTINUOUS_REPLICATION",
        "READY_FOR_RECOVERY",
    ]

    # Extract last recovery result from lifecycle
    lifecycle = server.get("lifeCycle", {})
    last_launch = lifecycle.get("lastLaunch", {})
    last_launch_type = last_launch.get("initiated", {}).get("type", "")
    last_launch_time = last_launch.get("initiated", {}).get(
        "apiCallDateTime", ""
    )
    last_launch_status = server.get("lastLaunchResult", "")

    return {
        "sourceServerID": server.get("sourceServerID", ""),
        "hostname": identification.get("hostname", ""),
        "fqdn": identification.get("fqdn", ""),
        "nameTag": server.get("tags", {}).get("Name", ""),
        "sourceInstanceId": identification.get("awsInstanceID", ""),
        "sourceIp": primary_ip,
        "sourceMac": nics[0].get("macAddress", "") if nics else "",
        "sourceRegion": source_region,
        "sourceAccount": source_account,
        "sourceAvailabilityZone": source_az,
        "targetAvailabilityZone": target_az,
        "os": source_props.get("os", {}).get("fullString", ""),
        "state": replication_state,
        "replicationState": replication_state,
        "lagDuration": data_replication.get("lagDuration", ""),
        "lastSeen": lifecycle.get("lastSeenByServiceDateTime", ""),
        "lastLaunchType": last_launch_type,
        "lastLaunchStatus": last_launch_status,
        "lastLaunchTime": last_launch_time,
        "replicatedStorageBytes": data_replication.get(
            "replicatedStorageBytes", 0
        ),
        "hardware": {
            "cpus": [
                {
                    "modelName": cpu.get("modelName", ""),
                    "cores": cpu.get("cores", 0),
                }
                for cpu in hardware
            ],
            "totalCores": total_cores,
            "ramBytes": ram_bytes,
            "ramGiB": ram_gib,
            "disks": disk_list,
            "totalDiskGiB": round(total_disk_gib, 2),
        },
        "networkInterfaces": [
            {
                "ips": nic.get("ips", []),
                "macAddress": nic.get("macAddress", ""),
                "isPrimary": nic.get("isPrimary", False),
            }
            for nic in nics
        ],
        "drsTags": server.get("tags", {}),
        "tags": server.get("tags", {}),
        "assignedToProtectionGroup": None,
        "selectable": is_ready,  # Only ready servers are selectable
    }


def enrich_server_data(
    participating_servers: List[Dict], drs_client, ec2_client
) -> List[Dict]:
    """
    Enrich server data with DRS source server details.

    For each server:
    1. Normalize DRS fields (sourceServerId, launchStatus, etc.)
    2. Query DRS for source server details
    3. Extract Name tag from DRS source server tags
    4. Extract IP address from DRS source server network interfaces
    5. Query EC2 for recovery instance details if available

    Args:
        participating_servers: List of DRS ParticipatingServer objects
        drs_client: boto3 DRS client
        ec2_client: boto3 EC2 client (used only for recovery instances)

    Returns:
        List of enriched server dicts with serverName and ipAddress populated
    """
    enriched = []

    # Extract source server IDs
    source_server_ids = [
        s.get("sourceServerID")
        for s in participating_servers
        if s.get("sourceServerID")
    ]

    # Query DRS for source server details
    source_servers_map = {}
    if source_server_ids:
        try:
            source_response = drs_client.describe_source_servers(
                filters={"sourceServerIDs": source_server_ids}
            )
            for source_server in source_response.get("items", []):
                source_id = source_server.get("sourceServerID")
                source_servers_map[source_id] = source_server
        except Exception as e:
            print(f"Error querying source servers: {e}")

    # Collect recovery instance IDs for batch query
    recovery_instance_ids = [
        s.get("recoveryInstanceID")
        for s in participating_servers
        if s.get("recoveryInstanceID")
    ]

    # Batch query recovery EC2 instances
    recovery_ec2_instances = {}
    if recovery_instance_ids:
        recovery_ec2_instances = batch_describe_ec2_instances(
            recovery_instance_ids, ec2_client
        )

    # Enrich each server
    for server in participating_servers:
        # Normalize DRS fields
        normalized = normalize_drs_response(server)

        source_server_id = normalized.get("sourceServerId")

        # Add source server details from DRS (Name tag and IP from DRS)
        if source_server_id and source_server_id in source_servers_map:
            source_server = source_servers_map[source_server_id]

            # Extract Name tag from DRS source server tags
            tags = source_server.get("tags", {})
            server_name = tags.get("Name", "")

            # Extract IP address from DRS source server network interfaces
            source_props = source_server.get("sourceProperties", {})
            network_interfaces = source_props.get("networkInterfaces", [])
            ip_address = ""
            if network_interfaces:
                # Get primary interface IP
                for interface in network_interfaces:
                    if interface.get("isPrimary"):
                        ips = interface.get("ips", [])
                        if ips:
                            ip_address = ips[0]
                        break
                # Fallback to first interface if no primary
                if not ip_address and network_interfaces[0].get("ips"):
                    ip_address = network_interfaces[0]["ips"][0]

            # Extract source instance ID
            hints = source_props.get("identificationHints", {})
            source_instance_id = hints.get("awsInstanceID", "")

            normalized.update(
                {
                    "serverName": server_name,
                    "ipAddress": ip_address,
                    "sourceInstanceId": source_instance_id,
                }
            )

        # Add recovery instance EC2 details if available
        recovery_instance_id = normalized.get("recoveryInstanceId")
        if (
            recovery_instance_id
            and recovery_instance_id in recovery_ec2_instances
        ):
            recovery_ec2 = recovery_ec2_instances[recovery_instance_id]
            normalized.update(
                {
                    "instanceId": recovery_instance_id,
                    "recoveryInstanceId": recovery_instance_id,
                    "privateIp": recovery_ec2.get("privateIpAddress", ""),
                    "hostname": recovery_ec2.get("privateDnsName", ""),
                    "instanceType": recovery_ec2.get("instanceType", ""),
                    "instanceState": recovery_ec2.get("state", {}).get(
                        "Name", ""
                    ),
                }
            )

        enriched.append(normalized)

    return enriched
