#!/usr/bin/env python3
"""
Delete and recreate Wave1-DatabaseServers protection group with correct account.
"""

import boto3
import json

AWS_PROFILE = "AWSAdministratorAccess-891376951562"
REGION = "us-east-2"
PROJECT_NAME = "hrp-drs-tech-adapter"
ENVIRONMENT = "dev"
ORCHESTRATION_ACCOUNT = "891376951562"

# Initialize AWS session
session = boto3.Session(profile_name=AWS_PROFILE)
lambda_client = session.client("lambda", region_name=REGION)
dynamodb = session.resource("dynamodb", region_name=REGION)

def get_existing_group():
    """Get existing protection group."""
    table = dynamodb.Table(f"{PROJECT_NAME}-protection-groups-{ENVIRONMENT}")
    
    response = table.scan()
    groups = response.get("Items", [])
    
    for group in groups:
        if group.get("groupName") == "Wave1-DatabaseServers":
            return group
    return None

def delete_protection_group(group_id):
    """Delete protection group via Lambda."""
    function_name = f"{PROJECT_NAME}-data-management-handler-{ENVIRONMENT}"
    
    print(f"Deleting protection group {group_id}...")
    
    event = {
        "operation": "delete_protection_group",
        "body": {
            "groupId": group_id
        }
    }
    
    try:
        invoke_response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )
        
        payload = json.loads(invoke_response["Payload"].read())
        
        if "error" in payload:
            print(f"✗ Error deleting: {payload.get('message', payload.get('error'))}")
            return False
        else:
            print(f"✓ Protection group deleted")
            return True
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def get_database_servers():
    """Get database servers from inventory."""
    inventory_table = dynamodb.Table(f"{PROJECT_NAME}-source-server-inventory-{ENVIRONMENT}")
    
    print("Fetching database servers from inventory...")
    
    response = inventory_table.scan()
    all_servers = response.get("Items", [])
    
    while "LastEvaluatedKey" in response:
        response = inventory_table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
        all_servers.extend(response.get("Items", []))
    
    database_servers = []
    for server in all_servers:
        hostname = server.get("hostname", "").lower()
        if "db" in hostname or "database" in hostname:
            database_servers.append(server)
    
    print(f"Found {len(database_servers)} database servers")
    return database_servers

def get_target_account():
    """Get target account from target accounts table."""
    table = dynamodb.Table(f"{PROJECT_NAME}-target-accounts-{ENVIRONMENT}")
    
    response = table.scan()
    accounts = response.get("Items", [])
    
    # Find the account that's not the current orchestration account
    for account in accounts:
        account_id = account.get("accountId")
        if account_id and account_id != ORCHESTRATION_ACCOUNT:
            print(f"Found target account: {account_id}")
            return account
    
    return None

def create_protection_group(database_servers, target_account):
    """Create protection group with target account context."""
    function_name = f"{PROJECT_NAME}-data-management-handler-{ENVIRONMENT}"
    
    server_ids = [s.get("sourceServerID") for s in database_servers if s.get("sourceServerID")]
    
    print(f"\nCreating protection group with {len(server_ids)} servers...")
    print(f"Target account: {target_account.get('accountId')}")
    print(f"Assume role: {target_account.get('assumeRoleName')}")
    
    event = {
        "operation": "create_protection_group",
        "body": {
            "groupName": "Wave1-DatabaseServers",
            "description": f"Wave 1 - All Database Servers ({len(server_ids)} servers)",
            "region": REGION,
            "accountId": target_account.get("accountId"),
            "assumeRoleName": target_account.get("assumeRoleName"),
            "sourceServerIds": server_ids
        }
    }
    
    try:
        invoke_response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType="RequestResponse",
            Payload=json.dumps(event)
        )
        
        payload = json.loads(invoke_response["Payload"].read())
        
        print(f"\nLambda response:")
        print(json.dumps(payload, indent=2))
        
        if "error" in payload:
            print(f"\n✗ Error: {payload.get('message', payload.get('error'))}")
            return None
        else:
            print(f"\n✓ Protection group created successfully")
            print(f"  Group ID: {payload.get('groupId')}")
            return payload
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    print("=" * 80)
    print("FIX WAVE1-DATABASESERVERS PROTECTION GROUP")
    print("=" * 80)
    print()
    
    # Check if group exists
    existing_group = get_existing_group()
    
    if existing_group:
        print(f"Found existing group: {existing_group.get('groupId')}")
        if not delete_protection_group(existing_group.get("groupId")):
            print("Failed to delete existing group")
            return
        print()
    
    # Get target account
    target_account = get_target_account()
    if not target_account:
        print("✗ No target account found")
        return
    
    # Get database servers
    database_servers = get_database_servers()
    if not database_servers:
        print("✗ No database servers found")
        return
    
    # Create protection group
    result = create_protection_group(database_servers, target_account)
    
    if result:
        print("\n" + "=" * 80)
        print("SUCCESS")
        print("=" * 80)
        print(f"Protection group created with {len(database_servers)} servers")
        print(f"\nView at: https://d1kqe40a9vwn47.cloudfront.net")
    else:
        print("\n" + "=" * 80)
        print("FAILED")
        print("=" * 80)

if __name__ == "__main__":
    main()
