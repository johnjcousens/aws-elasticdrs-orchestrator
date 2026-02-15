#!/usr/bin/env python3
"""
Check for REGION_STATUS records in the inventory table.
These should have been moved to the new DRSRegionStatusTable.
"""

import boto3
from boto3.dynamodb.conditions import Key

def check_region_status_records():
    """Check for REGION_STATUS records in inventory table."""
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
    
    if items:
        print("\nRecords found:")
        for item in items:
            pk = item.get('PK', 'Unknown')
            sk = item.get('SK', 'Unknown')
            print(f"  - PK: {pk}, SK: {sk}")
        
        print(f"\nThese {len(items)} records should be deleted.")
        print("They have been migrated to the new DRSRegionStatusTable.")
        
        return items
    else:
        print("\n✓ No REGION_STATUS records found in inventory table.")
        print("Cleanup is complete!")
        return []

if __name__ == '__main__':
    check_region_status_records()
