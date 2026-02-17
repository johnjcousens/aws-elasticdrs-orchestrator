#!/usr/bin/env python3
"""
Check execution in DynamoDB to verify it exists and get the correct planId.
"""
import boto3
import json
from decimal import Decimal

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super(DecimalEncoder, self).default(obj)

# Configuration
execution_id = "afd049ed-c370-49a5-a7f6-f9ace511ec98"
table_name = "hrp-drs-tech-adapter-execution-history-dev"
region = "us-east-2"
profile = "AWSAdministratorAccess-891376951562"

# Create DynamoDB client
session = boto3.Session(profile_name=profile, region_name=region)
dynamodb = session.resource("dynamodb")
table = dynamodb.Table(table_name)

print(f"Querying execution {execution_id} from {table_name}...")

# Query by executionId (partition key)
response = table.query(
    KeyConditionExpression=boto3.dynamodb.conditions.Key("executionId").eq(execution_id)
)

items = response.get("Items", [])
print(f"\nFound {len(items)} item(s)")

if items:
    execution = items[0]
    print(f"\n{'='*80}")
    print("EXECUTION DETAILS")
    print(f"{'='*80}")
    print(f"Execution ID: {execution.get('executionId')}")
    print(f"Plan ID: {execution.get('planId')}")
    print(f"Status: {execution.get('status')}")
    print(f"Execution Type: {execution.get('executionType')}")
    print(f"Start Time: {execution.get('startTime')}")
    print(f"Last Polled: {execution.get('lastPolledTime')}")
    
    # Wave details
    waves = execution.get("waves", [])
    print(f"\n{'='*80}")
    print(f"WAVES ({len(waves)} total)")
    print(f"{'='*80}")
    
    for i, wave in enumerate(waves, 1):
        print(f"\nWave {i}: {wave.get('waveName')}")
        print(f"  Status: {wave.get('status')}")
        print(f"  Job ID: {wave.get('jobId')}")
        print(f"  Region: {wave.get('region')}")
        
        servers = wave.get("serverStatuses", [])
        print(f"  Servers: {len(servers)}")
        
        if servers:
            print(f"  First server details:")
            first = servers[0]
            print(f"    Hostname: {first.get('hostname', 'N/A')}")
            print(f"    Source Server ID: {first.get('sourceServerId', 'N/A')}")
            print(f"    Recovery Instance ID: {first.get('recoveryInstanceId', 'N/A')}")
            print(f"    Instance Type: {first.get('instanceType', 'N/A')}")
            print(f"    Private IP: {first.get('privateIp', 'N/A')}")
            print(f"    Launch Status: {first.get('launchStatus', 'N/A')}")
    
    # Save full execution to file for inspection
    with open("execution_full.json", "w") as f:
        json.dump(execution, f, indent=2, cls=DecimalEncoder)
    print(f"\n✅ Full execution saved to execution_full.json")
    
else:
    print(f"\n❌ No execution found with ID: {execution_id}")
