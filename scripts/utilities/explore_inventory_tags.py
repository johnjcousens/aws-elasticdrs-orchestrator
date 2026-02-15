#!/usr/bin/env python3
"""
Explore what tags exist in the inventory and find database servers.
"""

import boto3
import json
from collections import defaultdict

AWS_PROFILE = "AWSAdministratorAccess-891376951562"
REGION = "us-east-2"
PROJECT_NAME = "hrp-drs-tech-adapter"
ENVIRONMENT = "dev"

# Initialize AWS session
session = boto3.Session(profile_name=AWS_PROFILE)
dynamodb = session.resource("dynamodb", region_name=REGION)

def explore_inventory():
    """Explore the inventory to understand tag structure."""
    inventory_table = dynamodb.Table(f"{PROJECT_NAME}-source-server-inventory-{ENVIRONMENT}")
    
    print("Scanning source server inventory...")
    
    # Scan the entire table
    response = inventory_table.scan()
    all_servers = response.get("Items", [])
    
    # Continue scanning if there are more items
    while "LastEvaluatedKey" in response:
        response = inventory_table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
        all_servers.extend(response.get("Items", []))
    
    print(f"Total servers in inventory: {len(all_servers)}")
    
    # Analyze accounts
    accounts = defaultdict(int)
    for server in all_servers:
        account_id = server.get("accountId", "Unknown")
        accounts[account_id] += 1
    
    print("\nServers by Account:")
    for account_id, count in sorted(accounts.items()):
        print(f"  {account_id}: {count} servers")
    
    # Analyze tag keys
    tag_keys = defaultdict(set)
    servers_with_tags = 0
    
    for server in all_servers:
        tags = server.get("tags", {})
        if tags:
            servers_with_tags += 1
            for tag_key, tag_value in tags.items():
                tag_keys[tag_key].add(tag_value)
    
    print(f"\nServers with tags: {servers_with_tags}")
    print(f"Unique tag keys: {len(tag_keys)}")
    
    print("\nAll Tag Keys and Values:")
    for tag_key in sorted(tag_keys.keys()):
        values = sorted(tag_keys[tag_key])
        print(f"\n  {tag_key}:")
        for value in values[:10]:  # Show first 10 values
            print(f"    - {value}")
        if len(values) > 10:
            print(f"    ... and {len(values) - 10} more values")
    
    # Look for database-related servers
    print("\n" + "=" * 80)
    print("LOOKING FOR DATABASE SERVERS")
    print("=" * 80)
    
    database_servers = []
    for server in all_servers:
        hostname = server.get("hostname", "").lower()
        tags = server.get("tags", {})
        
        # Check if it's a database server
        is_database = (
            "db" in hostname or
            "database" in hostname or
            "sql" in hostname or
            "mysql" in hostname or
            "postgres" in hostname or
            "oracle" in hostname or
            any("database" in str(v).lower() for v in tags.values()) or
            any("db" in str(v).lower() for v in tags.values())
        )
        
        if is_database:
            database_servers.append(server)
    
    print(f"\nFound {len(database_servers)} potential database servers")
    
    if database_servers:
        print("\nSample Database Servers (first 10):")
        for server in database_servers[:10]:
            print(f"\n  Hostname: {server.get('hostname')}")
            print(f"  Source Server ID: {server.get('sourceServerID')}")
            print(f"  Account: {server.get('accountId')}")
            tags = server.get("tags", {})
            if tags:
                print(f"  Tags:")
                for tag_key, tag_value in tags.items():
                    print(f"    {tag_key}: {tag_value}")
    
    # Look for wave-related tags
    print("\n" + "=" * 80)
    print("LOOKING FOR WAVE TAGS")
    print("=" * 80)
    
    wave_tags = {}
    for tag_key in tag_keys.keys():
        if "wave" in tag_key.lower():
            wave_tags[tag_key] = sorted(tag_keys[tag_key])
    
    if wave_tags:
        print("\nWave-related tags found:")
        for tag_key, values in wave_tags.items():
            print(f"\n  {tag_key}:")
            for value in values:
                # Count servers with this tag
                count = sum(1 for s in all_servers if s.get("tags", {}).get(tag_key) == value)
                print(f"    {value}: {count} servers")
    else:
        print("\n⚠ No wave-related tags found")
    
    return all_servers, database_servers

def main():
    print("=" * 80)
    print("INVENTORY EXPLORATION")
    print("=" * 80)
    print()
    
    all_servers, database_servers = explore_inventory()
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total Servers: {len(all_servers)}")
    print(f"Database Servers: {len(database_servers)}")

if __name__ == "__main__":
    main()
