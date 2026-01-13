#!/usr/bin/env python3
"""
Clean up duplicate PascalCase fields from DynamoDB items
Only removes the old PascalCase fields, keeps camelCase fields
"""

import boto3

def cleanup_protection_group_duplicates():
    """Remove duplicate PascalCase fields from protection groups"""
    
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('aws-elasticdrs-orchestrator-protection-groups-test')
    
    # Get the specific protection group
    group_id = "cb80616d-a024-4df3-b95f-873c00c94c15"
    
    try:
        response = table.get_item(Key={"groupId": group_id})
        if "Item" not in response:
            print(f"Protection group {group_id} not found")
            return
        
        item = response["Item"]
        print(f"Current item fields: {list(item.keys())}")
        
        # Fields to remove (old PascalCase versions)
        fields_to_remove = []
        
        # Check for duplicate fields
        if "ServerSelectionTags" in item and "serverSelectionTags" in item:
            fields_to_remove.append("ServerSelectionTags")
            print("Will remove duplicate ServerSelectionTags (keeping serverSelectionTags)")
        
        if "SourceServerIds" in item and "sourceServerIds" in item:
            fields_to_remove.append("SourceServerIds")
            print("Will remove duplicate SourceServerIds (keeping sourceServerIds)")
        
        if not fields_to_remove:
            print("No duplicate fields found")
            return
        
        # Remove the duplicate fields
        update_expression = "REMOVE " + ", ".join(fields_to_remove)
        
        print(f"Update expression: {update_expression}")
        
        # Confirm before executing
        confirm = input("Execute this cleanup? (y/N): ")
        if confirm.lower() != 'y':
            print("Cleanup cancelled")
            return
        
        table.update_item(
            Key={"groupId": group_id},
            UpdateExpression=update_expression
        )
        
        print("✅ Cleanup completed successfully")
        
        # Verify the cleanup
        response = table.get_item(Key={"groupId": group_id})
        item = response["Item"]
        print(f"Updated item fields: {list(item.keys())}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    cleanup_protection_group_duplicates()