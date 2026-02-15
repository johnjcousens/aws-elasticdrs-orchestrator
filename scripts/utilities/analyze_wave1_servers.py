#!/usr/bin/env python3
"""
Analyze servers with dr:wave=1 tag and collect all their tags.
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

def analyze_wave1_servers():
    """Find all servers with dr:wave=1 and collect their tags."""
    inventory_table = dynamodb.Table(f"{PROJECT_NAME}-source-server-inventory-{ENVIRONMENT}")
    
    print("Scanning source server inventory for dr:wave=1 servers...")
    
    # Scan the entire table
    response = inventory_table.scan()
    all_servers = response.get("Items", [])
    
    # Continue scanning if there are more items
    while "LastEvaluatedKey" in response:
        response = inventory_table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
        all_servers.extend(response.get("Items", []))
    
    print(f"Total servers in inventory: {len(all_servers)}")
    
    # Find servers with dr:wave=1
    wave1_servers = []
    all_tags = defaultdict(set)
    
    for server in all_servers:
        tags = server.get("tags", {})
        
        # Check if server has dr:wave=1
        if tags.get("dr:wave") == "1":
            wave1_servers.append(server)
            
            # Collect all tags from this server
            for tag_key, tag_value in tags.items():
                all_tags[tag_key].add(tag_value)
    
    print(f"\nServers with dr:wave=1: {len(wave1_servers)}")
    
    if wave1_servers:
        print("\n" + "=" * 80)
        print("WAVE 1 SERVERS")
        print("=" * 80)
        
        for server in wave1_servers:
            print(f"\nServer: {server.get('hostname', 'Unknown')}")
            print(f"  Source Server ID: {server.get('sourceServerID')}")
            print(f"  Account: {server.get('accountId')}")
            print(f"  Tags:")
            for tag_key, tag_value in server.get("tags", {}).items():
                print(f"    {tag_key}: {tag_value}")
        
        print("\n" + "=" * 80)
        print("ALL UNIQUE TAGS FROM WAVE 1 SERVERS")
        print("=" * 80)
        
        for tag_key in sorted(all_tags.keys()):
            values = sorted(all_tags[tag_key])
            print(f"\n{tag_key}:")
            for value in values:
                print(f"  - {value}")
        
        print("\n" + "=" * 80)
        print("PROTECTION GROUP TAG CRITERIA")
        print("=" * 80)
        print("\nTo create a protection group that includes all Wave 1 servers,")
        print("use these tag criteria:\n")
        
        tag_criteria = []
        for tag_key in sorted(all_tags.keys()):
            values = sorted(all_tags[tag_key])
            if len(values) == 1:
                tag_criteria.append(f'  "{tag_key}": "{values[0]}"')
            else:
                values_str = ", ".join(f'"{v}"' for v in values)
                tag_criteria.append(f'  "{tag_key}": [{values_str}]')
        
        print("{\n" + ",\n".join(tag_criteria) + "\n}")
        
        return wave1_servers, dict(all_tags)
    else:
        print("\n⚠ No servers found with dr:wave=1 tag")
        return [], {}

def main():
    print("=" * 80)
    print("WAVE 1 SERVER ANALYSIS")
    print("=" * 80)
    print()
    
    wave1_servers, all_tags = analyze_wave1_servers()
    
    if wave1_servers:
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Wave 1 Servers: {len(wave1_servers)}")
        print(f"Unique Tag Keys: {len(all_tags)}")
        print(f"Total Tag Combinations: {sum(len(values) for values in all_tags.values())}")

if __name__ == "__main__":
    main()
