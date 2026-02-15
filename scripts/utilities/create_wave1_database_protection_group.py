#!/usr/bin/env python3
"""
Create Wave1-DatabaseServers protection group with all database servers.
"""

import boto3
import json
from datetime import datetime
import uuid

AWS_PROFILE = "AWSAdministratorAccess-891376951562"
REGION = "us-east-2"
PROJECT_NAME = "hrp-drs-tech-adapter"
ENVIRONMENT = "dev"
ACCOUNT_ID = "891376951562"

# Initialize AWS session
session = boto3.Session(profile_name=AWS_PROFILE)
dynamodb = session.resource("dynamodb", region_name=REGION)
lambda_client = session.client("lambda", region_name=REGION)

def get_database_servers():
    """Get all database servers from inventory."""
    inventory_table = dynamodb.Table(f"{PROJECT_NAME}-source-server-inventory-{ENVIRONMENT}")
    
    print("Fetching database servers from inventory...")
    
    # Scan the entire table
    response = inventory_table.scan()
    all_servers = response.get("Items", [])
    
    # Continue scanning if there are more items
    while "LastEvaluatedKey" in response:
        response = inventory_table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
        all_servers.extend(response.get("Items", []))
    
    # Filter for database servers
    database_servers = []
    for server in all_servers:
        hostname = server.get("hostname", "").lower()
        if "db" in hostname or "database" in hostname:
            database_servers.append(server)
    
    print(f"Found {len(database_servers)} database servers")
    return database_servers

def create_protection_group(database_servers):
    """Create protection group via Lambda."""
    function_name = f"{PROJECT_NAME}-data-management-handler-{ENVIRONMENT}"
    
    # Extract server IDs
    server_ids = [server.get("sourceServerID") for server in database_servers if server.get("sourceServerID")]
    
    print(f"\nCreating protection group with {len(server_ids)} servers...")
    
    # Create protection group using direct invocation format
    event = {
        "operation": "create_protection_group",
        "body": {
            "groupName": "Wave1-DatabaseServers",
            "description": "Wave 1 - All Database Servers (100 servers)",
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
        
        print(f"Lambda response: {json.dumps(payload, indent=2)}")
        
        if invoke_response["StatusCode"] == 200:
            if "errorMessage" in payload:
                print(f"✗ Error: {payload['errorMessage']}")
                if "errorType" in payload:
                    print(f"  Type: {payload['errorType']}")
                return None
            else:
                print(f"✓ Protection group created successfully")
                print(f"  Group ID: {payload.get('groupId')}")
                return payload
        else:
            print(f"✗ Failed with status code: {invoke_response['StatusCode']}")
            return None
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def verify_protection_group():
    """Verify the protection group was created."""
    protection_groups_table = dynamodb.Table(f"{PROJECT_NAME}-protection-groups-{ENVIRONMENT}")
    
    try:
        response = protection_groups_table.scan()
        groups = response.get("Items", [])
        
        wave1_group = None
        for group in groups:
            if group.get("GroupName") == "Wave1-DatabaseServers":
                wave1_group = group
                break
        
        if wave1_group:
            print("\n" + "=" * 80)
            print("PROTECTION GROUP DETAILS")
            print("=" * 80)
            print(f"Group ID: {wave1_group.get('GroupId')}")
            print(f"Group Name: {wave1_group.get('GroupName')}")
            print(f"Description: {wave1_group.get('Description')}")
            print(f"Server Count: {len(wave1_group.get('ServerIds', []))}")
            print(f"Created: {wave1_group.get('CreatedAt')}")
            
            tags = wave1_group.get("Tags", {})
            if tags:
                print(f"\nTags:")
                for tag_key, tag_value in tags.items():
                    print(f"  {tag_key}: {tag_value}")
            
            return wave1_group
        else:
            print("\n⚠ Protection group not found in table")
            return None
            
    except Exception as e:
        print(f"\n✗ Error verifying: {e}")
        return None

def main():
    print("=" * 80)
    print("CREATE WAVE1-DATABASESERVERS PROTECTION GROUP")
    print("=" * 80)
    print()
    
    # Get database servers
    database_servers = get_database_servers()
    
    if not database_servers:
        print("✗ No database servers found")
        return
    
    # Show sample servers
    print("\nSample servers (first 5):")
    for server in database_servers[:5]:
        print(f"  - {server.get('hostname')} ({server.get('sourceServerID')})")
    print(f"  ... and {len(database_servers) - 5} more")
    
    # Create protection group
    result = create_protection_group(database_servers)
    
    if result:
        # Verify it was created
        verify_protection_group()
        
        print("\n" + "=" * 80)
        print("SUCCESS")
        print("=" * 80)
        print(f"Protection group 'Wave1-DatabaseServers' created with {len(database_servers)} servers")
    else:
        print("\n" + "=" * 80)
        print("FAILED")
        print("=" * 80)
        print("Protection group creation failed")

if __name__ == "__main__":
    main()
