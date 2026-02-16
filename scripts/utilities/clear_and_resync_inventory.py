#!/usr/bin/env python3
"""
Clear and re-sync the source server inventory table.

This script:
1. Clears all items from the inventory table
2. Re-syncs from target accounts only (not staging accounts)
3. Verifies the final count
"""

import boto3
import json
from botocore.exceptions import ClientError

AWS_PROFILE = "891376951562_AWSAdministratorAccess"
REGION = "us-east-2"
PROJECT_NAME = "hrp-drs-tech-adapter"
ENVIRONMENT = "dev"

# Initialize AWS session
session = boto3.Session(profile_name=AWS_PROFILE)
dynamodb = session.resource("dynamodb", region_name=REGION)
lambda_client = session.client("lambda", region_name=REGION)

def clear_inventory_table():
    """Clear all items from the inventory table."""
    table_name = f"{PROJECT_NAME}-source-server-inventory-{ENVIRONMENT}"
    table = dynamodb.Table(table_name)
    
    print(f"Clearing table: {table_name}")
    
    # Scan and delete all items
    scan_response = table.scan()
    items = scan_response.get("Items", [])
    
    print(f"Found {len(items)} items to delete")
    
    with table.batch_writer() as batch:
        for item in items:
            batch.delete_item(Key={
                "sourceServerArn": item["sourceServerArn"],
                "stagingAccountId": item["stagingAccountId"]
            })
    
    # Handle pagination
    while "LastEvaluatedKey" in scan_response:
        scan_response = table.scan(ExclusiveStartKey=scan_response["LastEvaluatedKey"])
        items = scan_response.get("Items", [])
        print(f"Found {len(items)} more items to delete")
        
        with table.batch_writer() as batch:
            for item in items:
                batch.delete_item(Key={
                    "sourceServerArn": item["sourceServerArn"],
                    "stagingAccountId": item["stagingAccountId"]
                })
    
    print("✓ Table cleared")

def sync_inventory():
    """Invoke Lambda to sync source server inventory."""
    function_name = f"{PROJECT_NAME}-query-handler-{ENVIRONMENT}"
    
    # Get target accounts
    print("\nFetching target accounts...")
    target_accounts_table = dynamodb.Table(f"{PROJECT_NAME}-target-accounts-{ENVIRONMENT}")
    response = target_accounts_table.scan()
    accounts = response.get("Items", [])
    
    print(f"Found {len(accounts)} target accounts")
    
    for account in accounts:
        account_id = account.get("accountId") or account.get("AccountId")
        account_name = account.get("accountName") or account.get("AccountName", "Unknown")
        
        print(f"\nSyncing inventory for account: {account_name} ({account_id})")
        
        event = {
            "operation": "sync_source_server_inventory",
            "accountId": account_id
        }
        
        try:
            invoke_response = lambda_client.invoke(
                FunctionName=function_name,
                InvocationType="RequestResponse",
                Payload=json.dumps(event)
            )
            
            payload = json.loads(invoke_response["Payload"].read())
            
            if invoke_response["StatusCode"] == 200:
                if "errorMessage" in payload:
                    print(f"  ✗ Error: {payload['errorMessage']}")
                else:
                    synced_count = payload.get("syncedServers", 0)
                    print(f"  ✓ Synced {synced_count} servers")
            else:
                print(f"  ✗ Failed with status code: {invoke_response['StatusCode']}")
                
        except ClientError as e:
            print(f"  ✗ AWS Error: {e}")
        except Exception as e:
            print(f"  ✗ Error: {e}")

def verify_inventory():
    """Verify the inventory table contents."""
    table_name = f"{PROJECT_NAME}-source-server-inventory-{ENVIRONMENT}"
    table = dynamodb.Table(table_name)
    
    print("\n" + "=" * 80)
    print("VERIFYING INVENTORY TABLE")
    print("=" * 80)
    
    # Count total items
    scan_response = table.scan(Select="COUNT")
    total_count = scan_response.get("Count", 0)
    
    while "LastEvaluatedKey" in scan_response:
        scan_response = table.scan(
            Select="COUNT",
            ExclusiveStartKey=scan_response["LastEvaluatedKey"]
        )
        total_count += scan_response.get("Count", 0)
    
    print(f"\nTotal servers in inventory: {total_count}")
    print(f"Expected: 303 (300 EC2 instances + 3 extended source servers)")
    
    if total_count == 303:
        print("✓ Count matches expected!")
    else:
        print(f"⚠ Count mismatch! Expected 303, got {total_count}")
    
    # Show breakdown by staging account
    print("\nBreakdown by staging account:")
    scan_response = table.scan()
    items = scan_response.get("Items", [])
    
    staging_counts = {}
    for item in items:
        staging_id = item.get("stagingAccountId", "unknown")
        staging_counts[staging_id] = staging_counts.get(staging_id, 0) + 1
    
    while "LastEvaluatedKey" in scan_response:
        scan_response = table.scan(ExclusiveStartKey=scan_response["LastEvaluatedKey"])
        items = scan_response.get("Items", [])
        for item in items:
            staging_id = item.get("stagingAccountId", "unknown")
            staging_counts[staging_id] = staging_counts.get(staging_id, 0) + 1
    
    for staging_id, count in sorted(staging_counts.items()):
        print(f"  {staging_id}: {count} servers")

def main():
    print("=" * 80)
    print("CLEAR AND RE-SYNC INVENTORY TABLE")
    print("=" * 80)
    print(f"Environment: {ENVIRONMENT}")
    print(f"Region: {REGION}")
    print()
    
    try:
        # Step 1: Clear table
        clear_inventory_table()
        
        # Step 2: Re-sync
        sync_inventory()
        
        # Step 3: Verify
        verify_inventory()
        
        print("\n" + "=" * 80)
        print("COMPLETE")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n✗ FAILED: {e}")
        raise

if __name__ == "__main__":
    main()
