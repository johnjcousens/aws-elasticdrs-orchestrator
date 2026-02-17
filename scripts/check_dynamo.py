#!/usr/bin/env python3
import boto3
import json
from boto3.dynamodb.conditions import Key

# Use the profile
session = boto3.Session(profile_name='AWSAdministratorAccess-891376951562')
dynamodb = session.resource('dynamodb', region_name='us-east-2')
table = dynamodb.Table('hrp-drs-tech-adapter-execution-history-dev')

# Query the execution
response = table.query(
    KeyConditionExpression=Key('executionId').eq('afd049ed-c370-49a5-a7f6-f9ace511ec98')
)

if response['Items']:
    execution = response['Items'][0]
    print(f"Execution Status: {execution.get('status', 'N/A')}")
    print(f"Plan ID: {execution.get('planId', 'N/A')}")
    print(f"\nWaves:")
    
    waves = execution.get('waves', [])
    for i, wave in enumerate(waves):
        print(f"\n  Wave {i+1}:")
        print(f"    Name: {wave.get('waveName', 'N/A')}")
        print(f"    Status: {wave.get('status', 'N/A')}")
        print(f"    Job ID: {wave.get('jobId', 'N/A')}")
        
        servers = wave.get('servers', [])
        print(f"    Servers: {len(servers)}")
        
        if servers:
            print(f"    First server sample:")
            server = servers[0]
            print(f"      - sourceServerId: {server.get('sourceServerId', 'N/A')}")
            print(f"      - serverName: {server.get('serverName', 'N/A')}")
            print(f"      - status: {server.get('status', 'N/A')}")
            print(f"      - recoveredInstanceId: {server.get('recoveredInstanceId', 'N/A')}")
            print(f"      - instanceType: {server.get('instanceType', 'N/A')}")
            print(f"      - privateIp: {server.get('privateIp', 'N/A')}")
            print(f"      - launchTime: {server.get('launchTime', 'N/A')}")
else:
    print("No execution found")
