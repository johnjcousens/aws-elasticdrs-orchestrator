#!/usr/bin/env python3
"""
Sync DRS tables with current AWS data.

This script:
1. Syncs source server inventory from all configured target accounts
2. Updates DRS region status for all regions
"""

import boto3
import json
from datetime import datetime
from botocore.exceptions import ClientError

AWS_PROFILE = "AWSAdministratorAccess-891376951562"
REGION = "us-east-2"
PROJECT_NAME = "hrp-drs-tech-adapter"
ENVIRONMENT = "dev"

# Initialize AWS session
session = boto3.Session(profile_name=AWS_PROFILE)
dynamodb = session.resource("dynamodb", region_name=REGION)
lambda_client = session.client("lambda", region_name=REGION)

def invoke_sync_source_server_inventory():
    """Invoke Lambda to sync source server inventory."""
    function_name = f"{PROJECT_NAME}-query-handler-{ENVIRONMENT}"
    
    # Get target accounts first
    print("Fetching target accounts...")
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

def update_drs_region_status():
    """Update DRS region status for all regions."""
    function_name = f"{PROJECT_NAME}-data-management-handler-{ENVIRONMENT}"
    
    # Common DRS regions
    drs_regions = [
        "us-east-1",
        "us-east-2",
        "us-west-1",
        "us-west-2",
        "eu-west-1",
        "eu-central-1",
        "ap-southeast-1",
        "ap-southeast-2",
        "ap-northeast-1",
    ]
    
    print("\nUpdating DRS region status...")
    
    for region in drs_regions:
        print(f"\nChecking region: {region}")
        
        event = {
            "operation": "update_drs_region_status",
            "region": region
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
                    status = payload.get("status", "unknown")
                    print(f"  ✓ Status: {status}")
            else:
                print(f"  ✗ Failed with status code: {invoke_response['StatusCode']}")
                
        except ClientError as e:
            print(f"  ✗ AWS Error: {e}")
        except Exception as e:
            print(f"  ✗ Error: {e}")

def verify_table_contents():
    """Verify the tables have data."""
    print("\n" + "=" * 80)
    print("VERIFYING TABLE CONTENTS")
    print("=" * 80)
    
    # Check source server inventory
    inventory_table = dynamodb.Table(f"{PROJECT_NAME}-source-server-inventory-{ENVIRONMENT}")
    inventory_response = inventory_table.scan(Limit=10)
    inventory_count = inventory_response.get("Count", 0)
    
    print(f"\nSource Server Inventory Table:")
    print(f"  Items (first 10): {inventory_count}")
    if inventory_count > 0:
        print(f"  Sample item: {json.dumps(inventory_response['Items'][0], indent=2, default=str)[:200]}...")
    
    # Check DRS region status
    region_status_table = dynamodb.Table(f"{PROJECT_NAME}-drs-region-status-{ENVIRONMENT}")
    region_response = region_status_table.scan(Limit=10)
    region_count = region_response.get("Count", 0)
    
    print(f"\nDRS Region Status Table:")
    print(f"  Items (first 10): {region_count}")
    if region_count > 0:
        print(f"  Sample item: {json.dumps(region_response['Items'][0], indent=2, default=str)[:200]}...")

def main():
    print("=" * 80)
    print("DRS TABLE SYNC")
    print("=" * 80)
    print(f"Environment: {ENVIRONMENT}")
    print(f"Region: {REGION}")
    print()
    
    try:
        # Sync source server inventory
        invoke_sync_source_server_inventory()
        
        # Update DRS region status
        update_drs_region_status()
        
        # Verify tables have data
        verify_table_contents()
        
        print("\n" + "=" * 80)
        print("SYNC COMPLETE")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n✗ SYNC FAILED: {e}")
        raise

if __name__ == "__main__":
    main()
