#!/usr/bin/env python3
"""
Delete REGION_STATUS records from the inventory table.
These records have been migrated to the new DRSRegionStatusTable.

Usage:
    python3 scripts/cleanup_region_status_records.py --dry-run  # Check what would be deleted
    python3 scripts/cleanup_region_status_records.py            # Actually delete
"""

import argparse
import boto3
from boto3.dynamodb.conditions import Key

def cleanup_region_status_records(dry_run=True):
    """Delete REGION_STATUS records from inventory table."""
    dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
    table = dynamodb.Table('hrp-drs-tech-adapter-source-server-inventory-dev')
    
    print("Scanning for REGION_STATUS records in inventory table...")
    
    # Scan for REGION_STATUS records
    response = table.scan(
        FilterExpression='begins_with(#pk, :prefix)',
        ExpressionAttributeNames={'#pk': 'PK'},
        ExpressionAttributeValues={':prefix': 'REGION_STATUS#'}
    )
    
    items = response.get('Items', [])
    print(f"\nFound {len(items)} REGION_STATUS records")
    
    if not items:
        print("\n✓ No REGION_STATUS records found in inventory table.")
        print("Cleanup is complete!")
        return
    
    print("\nRecords to delete:")
    for item in items:
        pk = item.get('PK', 'Unknown')
        sk = item.get('SK', 'Unknown')
        print(f"  - PK: {pk}, SK: {sk}")
    
    if dry_run:
        print(f"\n[DRY RUN] Would delete {len(items)} records")
        print("Run without --dry-run to actually delete")
        return
    
    # Delete records
    print(f"\nDeleting {len(items)} records...")
    deleted_count = 0
    
    with table.batch_writer() as batch:
        for item in items:
            pk = item.get('PK')
            sk = item.get('SK')
            if pk and sk:
                batch.delete_item(Key={'PK': pk, 'SK': sk})
                deleted_count += 1
    
    print(f"\n✓ Successfully deleted {deleted_count} REGION_STATUS records")
    print("These records have been migrated to DRSRegionStatusTable")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Delete REGION_STATUS records from inventory table'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be deleted without actually deleting'
    )
    
    args = parser.parse_args()
    cleanup_region_status_records(dry_run=args.dry_run)
