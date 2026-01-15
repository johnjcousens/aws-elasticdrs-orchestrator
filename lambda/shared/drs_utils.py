"""
AWS DRS utility functions for field normalization and data transformation.

Handles conversion between AWS DRS PascalCase responses and application camelCase.
"""

from typing import Any, Dict, List, Union


def normalize_drs_response(
    drs_data: Union[Dict, List], recursive: bool = True
) -> Union[Dict, List]:
    """
    Convert AWS DRS PascalCase fields to application camelCase.
    
    Transformation happens at API boundary only - never in database.
    Handles nested objects and lists recursively.
    
    Args:
        drs_data: Response from AWS DRS API
        recursive: Whether to normalize nested objects
        
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
            normalized[new_key] = normalize_drs_response(
                value, recursive=True
            )
        elif recursive and isinstance(value, list):
            normalized[new_key] = [
                normalize_drs_response(item, recursive=True)
                if isinstance(item, dict)
                else item
                for item in value
            ]
        else:
            normalized[new_key] = value

    return normalized


def extract_recovery_instance_details(
    drs_instance: Dict,
) -> Dict[str, Any]:
    """
    Extract and normalize recovery instance details from DRS API response.
    
    Args:
        drs_instance: Raw DRS recovery instance object
        
    Returns:
        Normalized instance details with required fields
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
    
    Args:
        source_server_ids: List of source server IDs to filter
        recovery_instance_ids: List of recovery instance IDs to filter
        
    Returns:
        Filter dict for DRS API calls
    """
    filters = {}

    if source_server_ids:
        filters["sourceServerIDs"] = source_server_ids

    if recovery_instance_ids:
        filters["recoveryInstanceIDs"] = recovery_instance_ids

    return filters
