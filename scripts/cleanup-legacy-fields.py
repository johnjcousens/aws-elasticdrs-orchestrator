#!/usr/bin/env python3
"""
Legacy Field Cleanup Script

This script removes old PascalCase fields from DynamoDB items that have
both PascalCase and camelCase versions of the same field.

Usage:
    python3 scripts/cleanup-legacy-fields.py --table-name protection-groups-table --item-id cb80616d-a024-4df3-b95f-873c00c94c15
"""

import boto3
import json
import argparse
from typing import Dict, List, Any

def cleanup_protection_group_legacy_fields(table_name: str, group_id: str, region: str = "us-east-1") -> Dict[str, Any]:
    """
    Clean up legacy PascalCase fields from a protection group item.
    
    Args:
        table_name: DynamoDB table name
        group_id: Protection group ID
        region: AWS region
        
    Returns:
        Dict with cleanup results
    """
    dynamodb = boto3.resource('dynamodb', region_name=region)
    table = dynamodb.Table(table_name)
    
    # Get current item
    response = table.get_item(Key={"groupId": group_id})
    if "Item" not in response:
        return {"error": "Item not found", "groupId": group_id}
    
    item = response["Item"]
    print(f"Current item fields: {list(item.keys())}")
    
    # Identify legacy PascalCase fields to remove
    legacy_fields_to_remove = []
    
    # Check for legacy fields that have camelCase equivalents
    legacy_mappings = {
        "GroupName": "groupName",
        "Description": "description", 
        "ServerSelectionTags": "serverSelectionTags",
        "SourceServerIds": "sourceServerIds",
        "CreatedDate": "createdDate",
        "LastModifiedDate": "lastModifiedDate"
    }
    
    for pascal_field, camel_field in legacy_mappings.items():
        if pascal_field in item and camel_field in item:
            legacy_fields_to_remove.append(pascal_field)
            print(f"Found duplicate field: {pascal_field} (legacy) and {camel_field} (current)")
            print(f"  Legacy value: {item[pascal_field]}")
            print(f"  Current value: {item[camel_field]}")
    
    if not legacy_fields_to_remove:
        return {"message": "No legacy fields found to clean up", "groupId": group_id}
    
    # Remove legacy fields
    print(f"\nRemoving legacy fields: {legacy_fields_to_remove}")
    
    try:
        # Use REMOVE operation to delete legacy PascalCase fields
        remove_expression = "REMOVE " + ", ".join(legacy_fields_to_remove)
        
        response = table.update_item(
            Key={"groupId": group_id},
            UpdateExpression=remove_expression,
            ReturnValues="ALL_NEW"
        )
        
        updated_item = response["Attributes"]
        print(f"\nCleanup successful! Remaining fields: {list(updated_item.keys())}")
        
        return {
            "success": True,
            "groupId": group_id,
            "removedFields": legacy_fields_to_remove,
            "remainingFields": list(updated_item.keys()),
            "updatedItem": updated_item
        }
        
    except Exception as e:
        print(f"Error during cleanup: {e}")
        return {
            "error": str(e),
            "groupId": group_id,
            "attemptedRemoval": legacy_fields_to_remove
        }

def main():
    parser = argparse.ArgumentParser(description="Clean up legacy PascalCase fields from DynamoDB items")
    parser.add_argument("--table-name", required=True, help="DynamoDB table name")
    parser.add_argument("--item-id", required=True, help="Item ID to clean up")
    parser.add_argument("--region", default="us-east-1", help="AWS region")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be removed without making changes")
    
    args = parser.parse_args()
    
    print(f"Cleaning up legacy fields for item {args.item_id} in table {args.table_name}")
    print(f"Region: {args.region}")
    print(f"Dry run: {args.dry_run}")
    print("-" * 60)
    
    if args.dry_run:
        print("DRY RUN MODE - No changes will be made")
        # TODO: Implement dry run logic
        return
    
    result = cleanup_protection_group_legacy_fields(args.table_name, args.item_id, args.region)
    
    print("\nCleanup Result:")
    print(json.dumps(result, indent=2, default=str))

if __name__ == "__main__":
    main()