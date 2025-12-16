"""
DRS Tag Synchronization Lambda
Syncs EC2 instance tags to DRS source servers on a schedule across all DRS regions.
"""

import boto3
import logging
import json
import os
from botocore.config import Config

logger = logging.getLogger()
logger.setLevel(logging.INFO)

config = Config(retries=dict(max_attempts=10))

# Source region where EC2 instances live (DRS doesn't provide this in API)
# Set via environment variable, defaults to us-east-1
SOURCE_REGION = os.environ.get('SOURCE_REGION', 'us-east-1')

# All 28 commercial AWS regions where DRS is available
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
]


def handler(event, context):
    """
    Main handler - syncs EC2 tags to DRS source servers across all regions.
    """
    logger.info(f"Starting DRS tag sync across {len(DRS_REGIONS)} regions")
    
    total_synced = 0
    total_servers = 0
    total_failed = 0
    regions_with_servers = []
    
    for region in DRS_REGIONS:
        try:
            result = sync_tags_in_region(region)
            if result['total'] > 0:
                regions_with_servers.append(region)
                total_servers += result['total']
                total_synced += result['synced']
                total_failed += result['failed']
                logger.info(f"{region}: {result['synced']}/{result['total']} synced")
        except Exception as e:
            # Log but continue - don't fail entire sync for one region
            logger.warning(f"{region}: skipped - {e}")
    
    summary = {
        'total_regions': len(DRS_REGIONS),
        'regions_with_servers': len(regions_with_servers),
        'total_servers': total_servers,
        'total_synced': total_synced,
        'total_failed': total_failed,
        'regions': regions_with_servers
    }
    
    logger.info(f"Tag sync complete: {total_synced}/{total_servers} servers synced across {len(regions_with_servers)} regions")
    
    return {
        'statusCode': 200,
        'body': json.dumps(summary)
    }


def sync_tags_in_region(drs_region: str) -> dict:
    """Sync EC2 tags to all DRS source servers in a single region."""
    drs_client = boto3.client('drs', region_name=drs_region, config=config)
    
    # Cache EC2 clients per source region
    ec2_clients = {}
    
    # Get all DRS source servers
    source_servers = get_source_servers(drs_client)
    logger.info(f"Found {len(source_servers)} DRS source servers")
    
    synced = 0
    failed = 0
    
    for server in source_servers:
        try:
            instance_id = server.get('sourceProperties', {}).get('identificationHints', {}).get('awsInstanceID')
            source_server_id = server['sourceServerID']
            server_arn = server['arn']
            
            # Get the source region where EC2 instance lives (from sourceCloudProperties.originRegion)
            source_region = server.get('sourceCloudProperties', {}).get('originRegion', drs_region)
            
            if not instance_id:
                logger.warning(f"No instance ID for source server {source_server_id}, skipping")
                continue
            
            # Skip disconnected servers
            replication_state = server.get('dataReplicationInfo', {}).get('dataReplicationState', '')
            if replication_state == 'DISCONNECTED':
                logger.info(f"Skipping disconnected server {source_server_id}")
                continue
            
            # Get or create EC2 client for source region
            if source_region not in ec2_clients:
                ec2_clients[source_region] = boto3.client('ec2', region_name=source_region, config=config)
            ec2_client = ec2_clients[source_region]
            
            # Get EC2 instance tags from SOURCE region
            ec2_tags = get_ec2_tags(ec2_client, instance_id)
            if not ec2_tags:
                logger.info(f"No tags found for EC2 instance {instance_id} in {source_region}")
                continue
            
            # Sync tags to DRS source server
            sync_server_tags(drs_client, server_arn, ec2_tags)
            
            # Enable copyTags in launch configuration
            enable_copy_tags(drs_client, source_server_id)
            
            synced += 1
            logger.info(f"Synced {len(ec2_tags)} tags from {source_region}:{instance_id} -> {source_server_id}")
            
        except Exception as e:
            failed += 1
            logger.error(f"Failed to sync server {server.get('sourceServerID', 'unknown')}: {e}")
    
    return {
        'total': len(source_servers),
        'synced': synced,
        'failed': failed,
        'region': drs_region
    }


def get_source_servers(drs_client) -> list:
    """Get all DRS source servers using pagination."""
    servers = []
    paginator = drs_client.get_paginator('describe_source_servers')
    
    for page in paginator.paginate(filters={}, maxResults=200):
        servers.extend(page.get('items', []))
    
    return servers


def get_ec2_tags(ec2_client, instance_id: str) -> dict:
    """Get tags from EC2 instance, excluding aws: reserved tags."""
    try:
        response = ec2_client.describe_instances(InstanceIds=[instance_id])
        
        if not response['Reservations']:
            return {}
        
        instance = response['Reservations'][0]['Instances'][0]
        tags = {}
        
        for tag in instance.get('Tags', []):
            key = tag['Key']
            # Skip AWS reserved tags
            if not key.startswith('aws:'):
                tags[key] = tag['Value']
        
        return tags
        
    except Exception as e:
        logger.error(f"Failed to get tags for instance {instance_id}: {e}")
        return {}


def sync_server_tags(drs_client, server_arn: str, tags: dict):
    """Apply tags to DRS source server."""
    if not tags:
        return
    
    drs_client.tag_resource(
        resourceArn=server_arn,
        tags=tags
    )


def enable_copy_tags(drs_client, source_server_id: str):
    """Enable copyTags in launch configuration so tags propagate to recovery instances."""
    try:
        drs_client.update_launch_configuration(
            sourceServerID=source_server_id,
            copyTags=True
        )
    except Exception as e:
        logger.warning(f"Failed to enable copyTags for {source_server_id}: {e}")
