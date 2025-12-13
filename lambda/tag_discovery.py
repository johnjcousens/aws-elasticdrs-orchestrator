"""
Tag Discovery Lambda
Discovers DRS source servers by tags for tag-based orchestration.
Supports single-account and multi-staging-account modes.
"""

import json
import os
import boto3
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# Environment variables
DEFAULT_REGION = os.environ.get('AWS_REGION', 'us-east-1')
STAGING_ACCOUNTS_PARAM = os.environ.get('STAGING_ACCOUNTS_PARAM', '')

# Valid replication states for recovery
VALID_REPLICATION_STATES = ['CONTINUOUS', 'INITIAL_SYNC', 'RESCAN']


def lambda_handler(event: Dict, context: Any) -> Dict:
    """
    Discover DRS source servers matching tags.
    
    Input:
    {
        "tags": {"DR-Wave": "1", "DR-Application": "HRP"},
        "region": "us-east-1",
        "executionId": "uuid",
        "stagingAccounts": [...]  # Optional, for multi-account
    }
    
    Output:
    {
        "executionId": "uuid",
        "totalServers": 150,
        "servers": [...],
        "serversByWave": {"1": [...], "2": [...]},
        "waveCount": 2,
        "healthyCount": 145,
        "unhealthyCount": 5
    }
    """
    print(f"Tag Discovery received: {json.dumps(event)}")
    
    input_tags = event.get('tags', {})
    region = event.get('region', DEFAULT_REGION)
    execution_id = event.get('executionId')
    staging_accounts = event.get('stagingAccounts', [])
    
    if not input_tags:
        return {
            'executionId': execution_id,
            'totalServers': 0,
            'servers': [],
            'error': 'No tags provided for server selection'
        }
    
    # Discover servers
    if staging_accounts:
        # Multi-staging-account mode
        result = discover_multi_account(input_tags, staging_accounts)
    else:
        # Single-account mode (current account)
        result = discover_single_account(input_tags, region)
    
    result['executionId'] = execution_id
    
    print(f"Discovered {result['totalServers']} servers matching tags")
    return result


def discover_single_account(tags: Dict[str, str], region: str) -> Dict:
    """
    Discover DRS source servers in the current account matching tags.
    
    Args:
        tags: Tag key-value pairs to match (AND logic)
        region: AWS region to query
    
    Returns:
        Discovery result with servers grouped by wave
    """
    drs = boto3.client('drs', region_name=region)
    
    matching_servers = []
    healthy_count = 0
    unhealthy_count = 0
    
    try:
        paginator = drs.get_paginator('describe_source_servers')
        
        for page in paginator.paginate():
            for server in page.get('items', []):
                server_tags = server.get('tags', {})
                
                # Check if all input tags match (AND logic)
                if all(server_tags.get(k) == v for k, v in tags.items()):
                    # Extract server details
                    source_props = server.get('sourceProperties', {})
                    id_hints = source_props.get('identificationHints', {})
                    replication_info = server.get('dataReplicationInfo', {})
                    replication_state = replication_info.get('dataReplicationState', 'UNKNOWN')
                    
                    # Determine health status
                    is_healthy = replication_state in VALID_REPLICATION_STATES
                    if is_healthy:
                        healthy_count += 1
                    else:
                        unhealthy_count += 1
                    
                    server_info = {
                        'sourceServerId': server['sourceServerID'],
                        'hostname': id_hints.get('hostname', 'unknown'),
                        'fqdn': id_hints.get('fqdn', ''),
                        'replicationState': replication_state,
                        'isHealthy': is_healthy,
                        'tags': server_tags,
                        'region': region,
                        'accountId': server.get('sourceServerID', '').split('/')[0] if '/' in server.get('sourceServerID', '') else None,
                        'lastLaunchResult': server.get('lastLaunchResult', 'NOT_STARTED'),
                        'lifeCycleState': server.get('lifeCycle', {}).get('state', 'UNKNOWN')
                    }
                    
                    # Add OS info if available
                    os_info = source_props.get('os', {})
                    if os_info:
                        server_info['os'] = {
                            'fullString': os_info.get('fullString', ''),
                        }
                    
                    matching_servers.append(server_info)
    
    except Exception as e:
        print(f"Error discovering servers in {region}: {str(e)}")
        return {
            'totalServers': 0,
            'servers': [],
            'serversByWave': {},
            'waveCount': 0,
            'healthyCount': 0,
            'unhealthyCount': 0,
            'error': str(e)
        }
    
    # Group servers by wave tag
    servers_by_wave = group_servers_by_wave(matching_servers)
    
    return {
        'totalServers': len(matching_servers),
        'servers': matching_servers,
        'serversByWave': servers_by_wave,
        'waveCount': len(servers_by_wave),
        'healthyCount': healthy_count,
        'unhealthyCount': unhealthy_count
    }


def discover_multi_account(tags: Dict[str, str], staging_accounts: List[Dict]) -> Dict:
    """
    Discover DRS source servers across multiple staging accounts.
    Uses cross-account IAM role assumption.
    
    Args:
        tags: Tag key-value pairs to match
        staging_accounts: List of account configs with roleArn and region
            [{"accountId": "123456789012", "roleArn": "arn:aws:iam::...", "region": "us-east-1"}]
    
    Returns:
        Aggregated discovery result from all accounts
    """
    all_servers = []
    total_healthy = 0
    total_unhealthy = 0
    errors = []
    
    def discover_in_account(account_config: Dict) -> Dict:
        """Discover servers in a single staging account"""
        account_id = account_config.get('accountId')
        role_arn = account_config.get('roleArn')
        region = account_config.get('region', DEFAULT_REGION)
        
        try:
            # Assume role in staging account
            sts = boto3.client('sts')
            assumed = sts.assume_role(
                RoleArn=role_arn,
                RoleSessionName=f'drs-discovery-{account_id}'
            )
            
            credentials = assumed['Credentials']
            
            # Create DRS client with assumed credentials
            drs = boto3.client(
                'drs',
                region_name=region,
                aws_access_key_id=credentials['AccessKeyId'],
                aws_secret_access_key=credentials['SecretAccessKey'],
                aws_session_token=credentials['SessionToken']
            )
            
            matching_servers = []
            healthy = 0
            unhealthy = 0
            
            paginator = drs.get_paginator('describe_source_servers')
            
            for page in paginator.paginate():
                for server in page.get('items', []):
                    server_tags = server.get('tags', {})
                    
                    if all(server_tags.get(k) == v for k, v in tags.items()):
                        source_props = server.get('sourceProperties', {})
                        id_hints = source_props.get('identificationHints', {})
                        replication_info = server.get('dataReplicationInfo', {})
                        replication_state = replication_info.get('dataReplicationState', 'UNKNOWN')
                        
                        is_healthy = replication_state in VALID_REPLICATION_STATES
                        if is_healthy:
                            healthy += 1
                        else:
                            unhealthy += 1
                        
                        server_info = {
                            'sourceServerId': server['sourceServerID'],
                            'hostname': id_hints.get('hostname', 'unknown'),
                            'fqdn': id_hints.get('fqdn', ''),
                            'replicationState': replication_state,
                            'isHealthy': is_healthy,
                            'tags': server_tags,
                            'region': region,
                            'accountId': account_id,
                            'stagingAccountId': account_id,
                            'lastLaunchResult': server.get('lastLaunchResult', 'NOT_STARTED'),
                            'lifeCycleState': server.get('lifeCycle', {}).get('state', 'UNKNOWN')
                        }
                        
                        matching_servers.append(server_info)
            
            return {
                'accountId': account_id,
                'servers': matching_servers,
                'healthy': healthy,
                'unhealthy': unhealthy,
                'error': None
            }
            
        except Exception as e:
            print(f"Error discovering in account {account_id}: {str(e)}")
            return {
                'accountId': account_id,
                'servers': [],
                'healthy': 0,
                'unhealthy': 0,
                'error': str(e)
            }
    
    # Discover in parallel across accounts
    with ThreadPoolExecutor(max_workers=min(10, len(staging_accounts))) as executor:
        futures = {executor.submit(discover_in_account, acc): acc for acc in staging_accounts}
        
        for future in as_completed(futures):
            result = future.result()
            all_servers.extend(result['servers'])
            total_healthy += result['healthy']
            total_unhealthy += result['unhealthy']
            if result['error']:
                errors.append({
                    'accountId': result['accountId'],
                    'error': result['error']
                })
    
    # Group all servers by wave
    servers_by_wave = group_servers_by_wave(all_servers)
    
    response = {
        'totalServers': len(all_servers),
        'servers': all_servers,
        'serversByWave': servers_by_wave,
        'waveCount': len(servers_by_wave),
        'healthyCount': total_healthy,
        'unhealthyCount': total_unhealthy,
        'accountsQueried': len(staging_accounts)
    }
    
    if errors:
        response['errors'] = errors
    
    return response


def group_servers_by_wave(servers: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Group servers by their DR-Wave tag.
    Servers without DR-Wave tag go to wave "1" by default.
    """
    servers_by_wave = {}
    
    for server in servers:
        wave = server.get('tags', {}).get('DR-Wave', '1')
        if wave not in servers_by_wave:
            servers_by_wave[wave] = []
        servers_by_wave[wave].append(server)
    
    # Sort waves numerically
    sorted_waves = {}
    for wave in sorted(servers_by_wave.keys(), key=lambda x: int(x) if x.isdigit() else 999):
        sorted_waves[wave] = servers_by_wave[wave]
    
    return sorted_waves


def resolve_protection_group(protection_group: Dict, region: str = None) -> Dict:
    """
    Resolve a Protection Group to actual server IDs.
    
    For EXPLICIT mode: returns sourceServerIds as-is
    For TAGS mode: queries DRS API to find matching servers
    
    Args:
        protection_group: Protection Group dict with SelectionMode
        region: AWS region (uses PG region if not specified)
    
    Returns:
        Dict with resolvedServerIds and server details
    """
    selection_mode = protection_group.get('SelectionMode', 'EXPLICIT')
    pg_region = region or protection_group.get('Region', DEFAULT_REGION)
    
    if selection_mode == 'EXPLICIT':
        # Return explicit server IDs directly
        server_ids = protection_group.get('sourceServerIds', [])
        return {
            'selectionMode': 'EXPLICIT',
            'resolvedServerIds': server_ids,
            'serverCount': len(server_ids),
            'region': pg_region
        }
    
    elif selection_mode == 'TAGS':
        # Discover servers by tags
        tags = protection_group.get('ServerSelectionTags', {})
        if not tags:
            return {
                'selectionMode': 'TAGS',
                'resolvedServerIds': [],
                'serverCount': 0,
                'error': 'No ServerSelectionTags defined',
                'region': pg_region
            }
        
        # Use single-account discovery
        result = discover_single_account(tags, pg_region)
        
        # Extract just the server IDs
        server_ids = [s['sourceServerId'] for s in result.get('servers', [])]
        
        return {
            'selectionMode': 'TAGS',
            'tags': tags,
            'resolvedServerIds': server_ids,
            'serverCount': len(server_ids),
            'servers': result.get('servers', []),
            'healthyCount': result.get('healthyCount', 0),
            'unhealthyCount': result.get('unhealthyCount', 0),
            'region': pg_region
        }
    
    else:
        return {
            'error': f'Unknown SelectionMode: {selection_mode}',
            'resolvedServerIds': [],
            'serverCount': 0
        }


def resolve_inline_plan(inline_plan: Dict, region: str = None) -> Dict:
    """
    Resolve an inline plan definition to actual server IDs.
    
    Used for automation invocations that define Protection Groups
    and Recovery Plans inline rather than referencing DynamoDB records.
    
    Args:
        inline_plan: Dict with protectionGroups and waves
        region: Default AWS region
    
    Returns:
        Resolved plan with actual server IDs per wave
    """
    resolved_groups = []
    
    # Resolve each inline Protection Group
    for pg in inline_plan.get('protectionGroups', []):
        pg_region = pg.get('region', region or DEFAULT_REGION)
        
        if pg.get('selectionMode') == 'TAGS':
            tags = pg.get('tags', {})
            result = discover_single_account(tags, pg_region)
            resolved_groups.append({
                'name': pg.get('name', 'Unnamed'),
                'selectionMode': 'TAGS',
                'tags': tags,
                'resolvedServerIds': [s['sourceServerId'] for s in result.get('servers', [])],
                'servers': result.get('servers', []),
                'region': pg_region
            })
        else:
            # Explicit server IDs
            resolved_groups.append({
                'name': pg.get('name', 'Unnamed'),
                'selectionMode': 'EXPLICIT',
                'resolvedServerIds': pg.get('serverIds', []),
                'region': pg_region
            })
    
    # Build resolved waves
    resolved_waves = []
    for wave in inline_plan.get('waves', []):
        pg_index = wave.get('protectionGroupIndex', 0)
        if pg_index < len(resolved_groups):
            resolved_pg = resolved_groups[pg_index]
            resolved_waves.append({
                'waveNumber': wave.get('waveNumber', 1),
                'waveName': wave.get('waveName', f"Wave {wave.get('waveNumber', 1)}"),
                'pauseBeforeWave': wave.get('pauseBeforeWave', False),
                'serverIds': resolved_pg['resolvedServerIds'],
                'serverCount': len(resolved_pg['resolvedServerIds']),
                'protectionGroupName': resolved_pg['name'],
                'region': resolved_pg['region']
            })
    
    total_servers = sum(len(w['serverIds']) for w in resolved_waves)
    
    return {
        'planName': inline_plan.get('planName', 'Inline Plan'),
        'protectionGroups': resolved_groups,
        'waves': resolved_waves,
        'totalWaves': len(resolved_waves),
        'totalServers': total_servers
    }