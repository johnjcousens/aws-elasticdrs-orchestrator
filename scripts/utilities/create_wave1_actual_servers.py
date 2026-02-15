#!/usr/bin/env python3
"""
Create Wave1-DatabaseServers protection group with actual DRS servers.
"""

import boto3
import json

AWS_PROFILE = "AWSAdministratorAccess-891376951562"
REGION = "us-east-2"
PROJECT_NAME = "hrp-drs-tech-adapter"
ENVIRONMENT = "dev"
ACCOUNT_ID = "891376951562"

# Initialize AWS session
session = boto3.Session(profile_name=AWS_PROFILE)
lambda_client = session.client("lambda", region_name=REGION)
drs_client = session.client("drs", region_name=REGION)

def get_actual_drs_servers():
    """Get actual DRS source servers."""
    print("Fetching actual DRS source servers...")
    
    response = drs_client.describe_source_servers()
    servers = response.get("items", [])
    
    print(f"Found {len(servers)} DRS source servers")
    return servers

def create_protection_group(servers):
    """Create protection group via Lambda."""
    function_name = f"{PROJECT_NAME}-data-management-handler-{ENVIRONMENT}"
    
    # Extract server IDs
    server_ids = [server.get("sourceServerID") for server in servers]
    
    print(f"\nCreating protection group with {len(server_ids)} servers...")
    print(f"Server IDs: {server_ids}")
    
    # Create protection group using direct invocation format
    event = {
        "operation": "create_protection_group",
        "body": {
            "groupName": "Wave1-DatabaseServers",
            "description": f"Wave 1 - Database Servers ({len(server_ids)} servers)",
            "region": REGION,
            "accountId": ACCOUNT_ID,
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
            print(f"  Group Name: {payload.get('groupName')}")
            return payload
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    print("=" * 80)
    print("CREATE WAVE1-DATABASESERVERS PROTECTION GROUP")
    print("=" * 80)
    print()
    
    # Get actual DRS servers
    servers = get_actual_drs_servers()
    
    if not servers:
        print("✗ No DRS servers found")
        return
    
    # Create protection group
    result = create_protection_group(servers)
    
    if result:
        print("\n" + "=" * 80)
        print("SUCCESS")
        print("=" * 80)
        print(f"Protection group 'Wave1-DatabaseServers' created with {len(servers)} servers")
        print(f"\nYou can view it at:")
        print(f"https://d1kqe40a9vwn47.cloudfront.net")
    else:
        print("\n" + "=" * 80)
        print("FAILED")
        print("=" * 80)
        print("Protection group creation failed")

if __name__ == "__main__":
    main()
