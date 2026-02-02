"""
Configuration merge utilities for per-server launch template customization.

This module provides functions to merge protection group defaults with
server-specific overrides, implementing the inheritance model where
server configurations take precedence over group defaults.

Validates: Requirements 6.1, 6.2, 6.5
"""

from typing import Dict, Any, List


def get_effective_launch_config(protection_group: Dict[str, Any], server_id: str) -> Dict[str, Any]:
    """
    Merge group defaults with server-specific overrides.

    This function implements the configuration inheritance model where:
    1. Start with protection group defaults (launchConfig)
    2. Apply server-specific overrides (servers[].launchTemplate)
    3. Server overrides take precedence over group defaults

    The useGroupDefaults flag controls merge behavior:
    - True: Partial override - merge only specified fields
    - False: Full override - replace all fields

    Args:
        protection_group: Protection group document containing:
            - launchConfig: Group-level default configuration
            - servers: Array of server-specific configurations
        server_id: Source server ID to get effective config for

    Returns:
        Dict containing the effective launch configuration with
        server overrides merged into group defaults.

    Example:
        >>> pg = {
        ...     "launchConfig": {
        ...         "subnetId": "subnet-xxx",
        ...         "instanceType": "c6a.large",
        ...         "securityGroupIds": ["sg-xxx"]
        ...     },
        ...     "servers": [{
        ...         "sourceServerId": "s-123",
        ...         "useGroupDefaults": True,
        ...         "launchTemplate": {
        ...             "staticPrivateIp": "10.0.1.100",
        ...             "instanceType": "c6a.xlarge"
        ...         }
        ...     }]
        ... }
        >>> config = get_effective_launch_config(pg, "s-123")
        >>> config["instanceType"]
        'c6a.xlarge'
        >>> config["subnetId"]
        'subnet-xxx'
        >>> config["staticPrivateIp"]
        '10.0.1.100'
    """
    # Start with group defaults (deep copy to avoid mutations)
    effective_config = protection_group.get("launchConfig", {}).copy()

    # Find server-specific configuration
    servers = protection_group.get("servers", [])
    server_config = next(
        (s for s in servers if s.get("sourceServerId") == server_id),
        None,
    )

    # If no server config found, return group defaults
    if not server_config:
        return effective_config

    # Get server overrides
    server_overrides = server_config.get("launchTemplate", {})

    # Check useGroupDefaults flag (defaults to True)
    use_group_defaults = server_config.get("useGroupDefaults", True)

    if use_group_defaults:
        # Partial override: merge only specified fields
        # Server overrides take precedence for specified fields
        for key, value in server_overrides.items():
            if value is not None:
                effective_config[key] = value
    else:
        # Full override: replace all fields
        # Start fresh with server config only
        effective_config = server_overrides.copy()

    return effective_config


def get_servers_with_custom_config(
    protection_group: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Get list of servers that have custom launch configurations.

    A server is considered to have custom configuration if:
    - useGroupDefaults is False, OR
    - launchTemplate contains at least one non-null field

    Args:
        protection_group: Protection group document containing
            servers array

    Returns:
        List of server configurations that have custom settings

    Example:
        >>> pg = {
        ...     "servers": [
        ...         {
        ...             "sourceServerId": "s-1",
        ...             "useGroupDefaults": True,
        ...             "launchTemplate": {"staticPrivateIp": "10.0.1.100"}
        ...         },
        ...         {
        ...             "sourceServerId": "s-2",
        ...             "useGroupDefaults": True,
        ...             "launchTemplate": {}
        ...         }
        ...     ]
        ... }
        >>> custom = get_servers_with_custom_config(pg)
        >>> len(custom)
        1
        >>> custom[0]["sourceServerId"]
        's-1'
    """
    servers = protection_group.get("servers", [])
    custom_servers = []

    for server in servers:
        use_defaults = server.get("useGroupDefaults", True)
        launch_template = server.get("launchTemplate", {})

        # Check if server has custom config
        has_custom_fields = any(value is not None for value in launch_template.values())

        if not use_defaults or has_custom_fields:
            custom_servers.append(server)

    return custom_servers


def get_servers_with_default_config(
    protection_group: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Get list of servers using only protection group defaults.

    A server uses defaults if:
    - useGroupDefaults is True, AND
    - launchTemplate is empty or contains only null values

    Args:
        protection_group: Protection group document containing
            servers array

    Returns:
        List of server configurations using only defaults

    Example:
        >>> pg = {
        ...     "servers": [
        ...         {
        ...             "sourceServerId": "s-1",
        ...             "useGroupDefaults": True,
        ...             "launchTemplate": {}
        ...         },
        ...         {
        ...             "sourceServerId": "s-2",
        ...             "useGroupDefaults": True,
        ...             "launchTemplate": {"staticPrivateIp": "10.0.1.100"}
        ...         }
        ...     ]
        ... }
        >>> defaults = get_servers_with_default_config(pg)
        >>> len(defaults)
        1
        >>> defaults[0]["sourceServerId"]
        's-1'
    """
    servers = protection_group.get("servers", [])
    default_servers = []

    for server in servers:
        use_defaults = server.get("useGroupDefaults", True)
        launch_template = server.get("launchTemplate", {})

        # Check if server uses only defaults
        has_custom_fields = any(value is not None for value in launch_template.values())

        if use_defaults and not has_custom_fields:
            default_servers.append(server)

    return default_servers


def get_custom_fields(protection_group: Dict[str, Any], server_id: str) -> List[str]:
    """
    Get list of field names that are customized for a server.

    Args:
        protection_group: Protection group document
        server_id: Source server ID

    Returns:
        List of field names that have custom values

    Example:
        >>> pg = {
        ...     "servers": [{
        ...         "sourceServerId": "s-1",
        ...         "launchTemplate": {
        ...             "staticPrivateIp": "10.0.1.100",
        ...             "instanceType": "c6a.xlarge"
        ...         }
        ...     }]
        ... }
        >>> fields = get_custom_fields(pg, "s-1")
        >>> sorted(fields)
        ['instanceType', 'staticPrivateIp']
    """
    servers = protection_group.get("servers", [])
    server_config = next(
        (s for s in servers if s.get("sourceServerId") == server_id),
        None,
    )

    if not server_config:
        return []

    launch_template = server_config.get("launchTemplate", {})
    return [key for key, value in launch_template.items() if value is not None]
