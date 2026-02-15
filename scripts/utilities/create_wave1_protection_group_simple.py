#!/usr/bin/env python3
"""Simple script to create Wave1-DatabaseServers protection group."""

import json
import boto3

# Get all database servers from inventory
dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
inventory_table = dynamodb.Table('hrp-drs-tech-adapter-source-server-inventory-dev')

print("Fetching database servers...")
response = inventory_table.scan(
    FilterExpression='contains(hostname, :db)',
    ExpressionAttributeValues={':db': 'db'}
)
servers = response['Items']
print(f"Found {len(servers)} database servers")

# Create protection group payload
server_ids = [s['sourceServerID'] for s in servers]

payload = {
    "operation": "create_protection_group",
    "body": {
        "groupName": "Wave1-DatabaseServers",
        "description": "Database servers for Wave 1 recovery",
        "sourceServerIds": server_ids,
        "accountId": "851725249649",
        "region": "us-east-2"
    }
}

# Invoke Lambda
lambda_client = boto3.client('lambda', region_name='us-east-2')
print("\nCreating protection group...")

response = lambda_client.invoke(
    FunctionName='hrp-drs-tech-adapter-data-management-handler-dev',
    InvocationType='RequestResponse',
    Payload=json.dumps(payload)
)

result = json.loads(response['Payload'].read())
print("\nResult:")
print(json.dumps(result, indent=2))
