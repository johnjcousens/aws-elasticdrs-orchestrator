#!/usr/bin/env python3
"""
Cleanup script to remove REGION_STATUS# records from the source server inventory table.

These records were moved to the dedicated DRS Region Status table and should no longer
exist in the inventory table.

Usage:
    python3 scripts/cleanup-region-status-records.py --environment dev --dry-run
    python3 scripts/cleanup-region-status-records.py --environment dev --execute
"""

import argparse
import boto3
from typing import List, Dict


def get_region_status_records(table_name: str, region: str = "us-east-2") -> List[Dict]:
    """
    Scan the inventory table for REGION_STATUS# records.
    
    Args:
        table_name: DynamoDB table name
        region: AWS region
        
    Returns:
        List of region status records to delete
    """
    dynamodb = boto3.resource("dynamodb", region_name=region)
    table = dynamodb.Table(table_name)
    
    records = []
    
    # Scan for REGION_STATUS# records
    response = table.scan(
        FilterExpression="begins_with(sourceServerArn, :prefix)",
        ExpressionAttributeValues={":prefix": "REGION_STATUS#"}
    )
    
    records.extend(response.get("Items", []))
    
    # Handle pagination
    while "LastEvaluatedKey" in response:
        response = table.scan(
            FilterExpression="begins_with(sourceServerArn, :prefix)",
            ExpressionAttributeValues={":prefix": "REGION_STATUS#"},
            ExclusiveStartKey=response["LastEvaluatedKey"]
        )
        records.extend(response.get("Items", []))
    
    return records


def delete_records(table_name: str, records: List[Dict], region: str = "us-east-2", dry_run: bool = True):
    """
    Delete region status records from the inventory table.
    
    Args:
        table_name: DynamoDB table name
        records: List of records to delete
        region: AWS region
        dry_run: If True, only print what would be deleted
    """
    if not records:
        print("No REGION_STATUS# records found to delete")
        return
    
    print(f"\nFound {len(records)} REGION_STATUS# records to delete:")
    for record in records:
        print(f"  - {record['sourceServerArn']} (stagingAccountId: {record['stagingAccountId']})")
    
    if dry_run:
        print("\n[DRY RUN] No records were deleted. Use --execute to delete.")
        return
    
    # Delete records
    dynamodb = boto3.resource("dynamodb", region_name=region)
    table = dynamodb.Table(table_name)
    
    deleted_count = 0
    with table.batch_writer() as batch:
        for record in records:
            batch.delete_item(
                Key={
                    "sourceServerArn": record["sourceServerArn"],
                    "stagingAccountId": record["stagingAccountId"]
                }
            )
            deleted_count += 1
    
    print(f"\n✓ Deleted {deleted_count} REGION_STATUS# records from {table_name}")


def main():
    parser = argparse.ArgumentParser(
        description="Cleanup REGION_STATUS# records from source server inventory table"
    )
    parser.add_argument(
        "--environment",
        required=True,
        choices=["dev", "test", "staging", "prod"],
        help="Environment to clean up"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually delete the records"
    )
    parser.add_argument(
        "--region",
        default="us-east-2",
        help="AWS region (default: us-east-2)"
    )
    
    args = parser.parse_args()
    
    if not args.dry_run and not args.execute:
        parser.error("Must specify either --dry-run or --execute")
    
    # Construct table name
    table_name = f"hrp-drs-tech-adapter-source-server-inventory-{args.environment}"
    
    print(f"Scanning {table_name} for REGION_STATUS# records...")
    
    # Get records
    records = get_region_status_records(table_name, args.region)
    
    # Delete records
    delete_records(table_name, records, args.region, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
