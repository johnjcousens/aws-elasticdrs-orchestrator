"""
DRS Tag Synchronization Lambda
Syncs EC2 instance tags to DRS source servers on a schedule across all DRS regions.

Based on working archive implementation from December 2025.
"""

import boto3
import json
import logging
import os
import time
from botocore.config import Config
from typing import Dict, List, Any

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Boto3 configuration with retries
config = Config(retries=dict(max_attempts=10))

# All 30 commercial AWS regions where DRS is available (updated 2026)
DRS_REGIONS = [
    # Americas (6)
    'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2', 'ca-central-1', 'sa-east-1',
    # Europe (8)
    'eu-west-1', 'eu-west-2', 'eu-west-3', 'eu-central-1', 'eu-central-2',
    'eu-north-1', 'eu-south-1', 'eu-south-2',
    # Asia Pacific (10)
    'ap-northeast-1', 'ap-northeast-2', 'ap-northeast-3', 'ap-southeast-1',
    'ap-southeast-2', 'ap-southeast-3', 'ap-southeast-4', 'ap-south-1', 'ap-south-2', 'ap-east-1',
    # Middle East & Africa (4)
    'me-south-1', 'me-central-1', 'af-south-1', 'il-central-1',
    # GovCloud (2)
    'us-gov-east-1', 'us-gov-west-1',
]

# AWS reserved tag prefixes to exclude
AWS_RESERVED_TAGS = ['aws:', 'AWS:']


def lambda_handler(event, context):
    """
    Main handler - syncs EC2 tags to DRS source servers across all regions.
    
    Supports both EventBridge scheduled execution and manual API triggers.
    """
    logger.info(f"Starting DRS tag sync across {len(DRS_REGIONS)} regions")
    logger.info(f"Event: {json.dumps(event)}")
    
    # Determine trigger source
    trigger_source = "manual"
    if event.get('source') == 'aws.events':
        trigger_source = "eventbridge"
    elif event.get('detail-type') == 'Scheduled Event':
        trigger_source = "eventbridge"
    
    logger.info(f"Tag sync triggered by: {trigger_source}")
    
    total_synced = 0
    total_servers = 0
    total_failed = 0
    regions_with_servers = []
    region_results = {}
    
    start_time = time.time()
    
    for region in DRS_REGIONS:
        try:
            logger.info(f"Processing region: {region}")
            result = sync_tags_in_region(region)
            
            region_results[region] = result
            
            if result['total'] > 0:
                regions_with_servers.append(region)
                total_servers += result['total']
                total_synced += result['synced']
                total_failed += result['failed']
                logger.info(f"{region}: {result['synced']}/{result['total']} synced, {result['failed']} failed")
            else:
                logger.info(f"{region}: no DRS servers found")
                
        except Exception as e:
            # Log but continue - don't fail entire sync for one region
            logger.warning(f"{region}: skipped - {str(e)}")
            region_results[region] = {
                'total': 0,
                'synced': 0,
                'failed': 0,
                'error': str(e)
            }
    
    end_time = time.time()
    duration = round(end_time - start_time, 2)
    
    summary = {
        'trigger_source': trigger_source,
        'total_regions_processed': len(DRS_REGIONS),
        'regions_with_servers': len(regions_with_servers),
        'total_servers': total_servers,
        'total_synced': total_synced,
        'total_failed': total_failed,
        'success_rate': round((total_synced / total_servers * 100) if total_servers > 0 else 100, 2),
        'duration_seconds': duration,
        'regions': regions_with_servers,
        'timestamp': int(time.time())
    }
    
    logger.info(f"Tag sync complete: {total_synced}/{total_servers} servers synced across {len(regions_with_servers)} regions in {duration}s")
    
    return {
        'statusCode': 200,
        'body': json.dumps(summary),
        'summary': summary,
        'region_results': region_results
    }


def sync_tags_in_region(drs_region: str) -> Dict[str, int]:
    """
    Sync EC2 tags to all DRS source servers in a single region.
    
    Args:
        drs_region: AWS region where DRS source servers are located
        
    Returns:
        Dict with sync statistics: total, synced, failed
    """
    try:
        drs_client = boto3.client('drs', region_name=drs_region, config=config)
        
        # Get all DRS source servers in the region
        source_servers = get_source_servers(drs_client)
        
        if not source_servers:
            return {'total': 0, 'synced': 0, 'failed': 0}
        
        logger.info(f"Found {len(source_servers)} DRS source servers in {drs_region}")
        
        synced = 0
        failed = 0
        
        for server in source_servers:
            try:
                if sync_server_tags(server, drs_client, drs_region):
                    synced += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"Failed to sync tags for server {server.get('sourceServerID', 'unknown')}: {str(e)}")
                failed += 1
        
        return {
            'total': len(source_servers),
            'synced': synced,
            'failed': failed
        }
        
    except Exception as e:
        logger.error(f"Error syncing tags in region {drs_region}: {str(e)}")
        raise


def get_source_servers(drs_client) -> List[Dict]:
    """Get all DRS source servers using pagination."""
    source_servers = []
    
    try:
        paginator = drs_client.get_paginator('describe_source_servers')
        
        for page in paginator.paginate():
            servers = page.get('items', [])
            source_servers.extend(servers)
            
    except Exception as e:
        logger.error(f"Error getting source servers: {str(e)}")
        raise
    
    return source_servers


def sync_server_tags(server: Dict, drs_client, drs_region: str) -> bool:
    """
    Sync EC2 instance tags to a single DRS source server.
    
    Args:
        server: DRS source server object
        drs_client: DRS boto3 client
        drs_region: DRS region
        
    Returns:
        bool: True if sync successful, False otherwise
    """
    try:
        source_server_id = server.get('sourceServerID')
        server_arn = server.get('arn')
        
        if not source_server_id or not server_arn:
            logger.warning(f"Server missing required fields: {server}")
            return False
        
        # Get EC2 instance ID and source region
        source_properties = server.get('sourceProperties', {})
        identification_hints = source_properties.get('identificationHints', {})
        instance_id = identification_hints.get('awsInstanceID')
        
        # Get source region from sourceCloudProperties
        source_cloud_properties = server.get('sourceCloudProperties', {})
        source_region = source_cloud_properties.get('originRegion', drs_region)
        
        if not instance_id:
            logger.warning(f"Server {source_server_id} has no EC2 instance ID")
            return False
        
        # Get EC2 instance tags from source region
        ec2_tags = get_ec2_instance_tags(instance_id, source_region)
        
        if not ec2_tags:
            logger.info(f"Server {source_server_id} (instance {instance_id}) has no EC2 tags to sync")
            return True  # Not a failure - just no tags
        
        # Filter out AWS reserved tags
        filtered_tags = {k: v for k, v in ec2_tags.items() 
                        if not any(k.startswith(prefix) for prefix in AWS_RESERVED_TAGS)}
        
        if not filtered_tags:
            logger.info(f"Server {source_server_id} has only AWS reserved tags, skipping")
            return True
        
        # Apply tags to DRS source server
        try:
            drs_client.tag_resource(
                resourceArn=server_arn,
                tags=filtered_tags
            )
            
            logger.info(f"Synced {len(filtered_tags)} tags to server {source_server_id}: {list(filtered_tags.keys())}")
            
            # Enable copyTags so tags propagate to recovery instances
            try:
                drs_client.update_launch_configuration(
                    sourceServerID=source_server_id,
                    copyTags=True
                )
                logger.debug(f"Enabled copyTags for server {source_server_id}")
            except Exception as e:
                logger.warning(f"Could not enable copyTags for server {source_server_id}: {str(e)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply tags to server {source_server_id}: {str(e)}")
            return False
            
    except Exception as e:
        logger.error(f"Error syncing server tags: {str(e)}")
        return False


def get_ec2_instance_tags(instance_id: str, region: str) -> Dict[str, str]:
    """
    Get tags from EC2 instance.
    
    Args:
        instance_id: EC2 instance ID
        region: AWS region where EC2 instance is located
        
    Returns:
        Dict of tag key-value pairs
    """
    try:
        ec2_client = boto3.client('ec2', region_name=region, config=config)
        
        response = ec2_client.describe_instances(InstanceIds=[instance_id])
        
        reservations = response.get('Reservations', [])
        if not reservations:
            logger.warning(f"No reservations found for instance {instance_id}")
            return {}
        
        instances = reservations[0].get('Instances', [])
        if not instances:
            logger.warning(f"No instances found for instance {instance_id}")
            return {}
        
        instance = instances[0]
        tags = instance.get('Tags', [])
        
        # Convert tag list to dictionary
        tag_dict = {tag['Key']: tag['Value'] for tag in tags}
        
        logger.debug(f"Found {len(tag_dict)} tags for instance {instance_id}: {list(tag_dict.keys())}")
        
        return tag_dict
        
    except Exception as e:
        logger.error(f"Error getting EC2 tags for instance {instance_id} in region {region}: {str(e)}")
        return {}