#!/usr/bin/env python3
"""
Trigger poll operation for paused execution to populate recovery instance data.
"""
import boto3
import json

# Configuration
execution_id = "afd049ed-c370-49a5-a7f6-f9ace511ec98"
plan_id = "3301422d-58e9-47d6-9b41-5f5ce07c3eb4"  # Correct planId from DynamoDB
function_name = "hrp-drs-tech-adapter-execution-handler-dev"
region = "us-east-2"
profile = "AWSAdministratorAccess-891376951562"

# Create Lambda client
session = boto3.Session(profile_name=profile, region_name=region)
lambda_client = session.client("lambda")

# Create poll event
poll_event = {
    "operation": "poll",
    "executionId": execution_id,
    "planId": plan_id
}

print(f"Invoking poll operation for execution {execution_id}...")
print(f"Event: {json.dumps(poll_event, indent=2)}")

# Invoke Lambda
response = lambda_client.invoke(
    FunctionName=function_name,
    InvocationType="RequestResponse",
    Payload=json.dumps(poll_event)
)

# Parse response
payload = json.loads(response["Payload"].read())
print(f"\nResponse Status Code: {response['StatusCode']}")
print(f"Response Payload: {json.dumps(payload, indent=2)}")

if payload.get("statusCode") == 200:
    print("\n✅ Poll operation completed successfully!")
    print(f"Execution Status: {payload.get('status')}")
    print(f"All Waves Complete: {payload.get('allWavesComplete')}")
    
    # Show wave details
    waves = payload.get("waves", [])
    for wave in waves:
        wave_name = wave.get("waveName", "Unknown")
        wave_status = wave.get("status", "Unknown")
        server_count = len(wave.get("serverStatuses", []))
        print(f"\nWave: {wave_name}")
        print(f"  Status: {wave_status}")
        print(f"  Servers: {server_count}")
        
        # Show first server details if available
        servers = wave.get("serverStatuses", [])
        if servers:
            first_server = servers[0]
            print(f"  First Server:")
            print(f"    Hostname: {first_server.get('hostname', 'N/A')}")
            print(f"    Instance ID: {first_server.get('recoveryInstanceId', 'N/A')}")
            print(f"    Instance Type: {first_server.get('instanceType', 'N/A')}")
            print(f"    Private IP: {first_server.get('privateIp', 'N/A')}")
            print(f"    Launch Status: {first_server.get('launchStatus', 'N/A')}")
else:
    print(f"\n❌ Poll operation failed with status code: {payload.get('statusCode')}")
    body = payload.get('body', '{}')
    if isinstance(body, str):
        body = json.loads(body)
    print(f"Error: {body.get('error', 'Unknown error')}")
    print(f"Message: {body.get('message', 'No message')}")
