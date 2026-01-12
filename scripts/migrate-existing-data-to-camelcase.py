#!/usr/bin/env python3
"""
Migrate existing DynamoDB items from PascalCase to camelCase fields.

This script updates existing database items that still have PascalCase field names
(CreatedDate, LastModifiedDate, Version, Owner) to use camelCase field names
(createdDate, lastModifiedDate, version, owner).

Usage:
    python scripts/migrate-existing-data-to-camelcase.py --table-name protection-groups-table --dry-run
    python scripts/migrate-existing-data-to-camelcase.py --table-name protection-groups-table --execute
"""

import argparse
import boto3
from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError
import json
import sys

def migrate_protection_groups_table(table_name: str, dry_run: bool = True):
    """Migrate protection groups table from PascalCase to camelCase fields."""
    
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    
    print(f"🔍 Scanning table: {table_name}")
    
    # Scan for items with PascalCase fields
    response = table.scan()
    items = response.get('Items', [])
    
    # Handle pagination
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response.get('Items', []))
    
    print(f"📊 Found {len(items)} total items")
    
    # Find items that need migration (have PascalCase fields)
    items_to_migrate = []
    for item in items:
        needs_migration = False
        migration_plan = {}
        
        # Check for PascalCase fields that need to be converted
        if 'CreatedDate' in item and 'createdDate' not in item:
            migration_plan['createdDate'] = item['CreatedDate']
            migration_plan['remove_CreatedDate'] = True
            needs_migration = True
            
        if 'LastModifiedDate' in item and 'lastModifiedDate' not in item:
            migration_plan['lastModifiedDate'] = item['LastModifiedDate']
            migration_plan['remove_LastModifiedDate'] = True
            needs_migration = True
            
        if 'Version' in item and 'version' not in item:
            migration_plan['version'] = item['Version']
            migration_plan['remove_Version'] = True
            needs_migration = True
            
        if 'Owner' in item and 'owner' not in item:
            migration_plan['owner'] = item['Owner']
            migration_plan['remove_Owner'] = True
            needs_migration = True
        
        if needs_migration:
            items_to_migrate.append({
                'item': item,
                'migration_plan': migration_plan
            })
    
    print(f"🎯 Found {len(items_to_migrate)} items that need migration")
    
    if not items_to_migrate:
        print("✅ No items need migration - all items already use camelCase fields")
        return
    
    # Show migration plan
    print("\n📋 Migration Plan:")
    for i, migration_item in enumerate(items_to_migrate[:5]):  # Show first 5
        item = migration_item['item']
        plan = migration_item['migration_plan']
        print(f"  {i+1}. {item.get('groupId', 'unknown')} ({item.get('groupName', 'unknown')})")
        for field, value in plan.items():
            if not field.startswith('remove_'):
                print(f"     + Add {field}: {value}")
        for field in plan.keys():
            if field.startswith('remove_'):
                old_field = field.replace('remove_', '')
                print(f"     - Remove {old_field}")
    
    if len(items_to_migrate) > 5:
        print(f"  ... and {len(items_to_migrate) - 5} more items")
    
    if dry_run:
        print(f"\n🔍 DRY RUN MODE - No changes will be made")
        print(f"   Run with --execute to perform the migration")
        return
    
    # Confirm execution
    print(f"\n⚠️  EXECUTE MODE - This will modify {len(items_to_migrate)} items")
    confirm = input("Type 'yes' to proceed: ")
    if confirm.lower() != 'yes':
        print("❌ Migration cancelled")
        return
    
    # Perform migration
    print(f"\n🚀 Starting migration of {len(items_to_migrate)} items...")
    
    success_count = 0
    error_count = 0
    
    for i, migration_item in enumerate(items_to_migrate):
        item = migration_item['item']
        plan = migration_item['migration_plan']
        group_id = item.get('groupId', 'unknown')
        
        try:
            # Build update expression
            update_expression_parts = []
            expression_attribute_values = {}
            expression_attribute_names = {}
            remove_expression_parts = []
            
            # Add new camelCase fields
            for field, value in plan.items():
                if not field.startswith('remove_'):
                    # Handle reserved keywords
                    if field in ['owner', 'version']:
                        attr_name = f"#{field}"
                        expression_attribute_names[attr_name] = field
                        update_expression_parts.append(f"{attr_name} = :{field}")
                    else:
                        update_expression_parts.append(f"{field} = :{field}")
                    expression_attribute_values[f":{field}"] = value
            
            # Remove old PascalCase fields
            for field in plan.keys():
                if field.startswith('remove_'):
                    old_field = field.replace('remove_', '')
                    # Handle reserved keywords
                    if old_field in ['Owner', 'Version']:
                        attr_name = f"#{old_field}"
                        expression_attribute_names[attr_name] = old_field
                        remove_expression_parts.append(attr_name)
                    else:
                        remove_expression_parts.append(old_field)
            
            # Build complete update expression
            update_expression = ""
            if update_expression_parts:
                update_expression += "SET " + ", ".join(update_expression_parts)
            if remove_expression_parts:
                if update_expression:
                    update_expression += " "
                update_expression += "REMOVE " + ", ".join(remove_expression_parts)
            
            # Perform update
            update_params = {
                'Key': {'groupId': group_id},
                'UpdateExpression': update_expression,
                'ReturnValues': 'UPDATED_NEW'
            }
            
            if expression_attribute_values:
                update_params['ExpressionAttributeValues'] = expression_attribute_values
            
            if expression_attribute_names:
                update_params['ExpressionAttributeNames'] = expression_attribute_names
            
            response = table.update_item(**update_params)
            
            success_count += 1
            print(f"  ✅ {i+1}/{len(items_to_migrate)} - Updated {group_id}")
            
        except Exception as e:
            error_count += 1
            print(f"  ❌ {i+1}/{len(items_to_migrate)} - Failed {group_id}: {e}")
    
    print(f"\n🎉 Migration completed!")
    print(f"   ✅ Success: {success_count}")
    print(f"   ❌ Errors: {error_count}")
    
    if error_count == 0:
        print(f"   🎯 All items successfully migrated to camelCase!")

def main():
    parser = argparse.ArgumentParser(description='Migrate DynamoDB items to camelCase fields')
    parser.add_argument('--table-name', required=True, help='DynamoDB table name')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be changed without making changes')
    parser.add_argument('--execute', action='store_true', help='Actually perform the migration')
    
    args = parser.parse_args()
    
    if not args.dry_run and not args.execute:
        print("❌ Must specify either --dry-run or --execute")
        sys.exit(1)
    
    if args.dry_run and args.execute:
        print("❌ Cannot specify both --dry-run and --execute")
        sys.exit(1)
    
    try:
        migrate_protection_groups_table(args.table_name, dry_run=args.dry_run)
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()