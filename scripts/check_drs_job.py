#!/usr/bin/env python3
import boto3
import json

# Use the profile
session = boto3.Session(profile_name='AWSAdministratorAccess-891376951562')
drs_client = session.client('drs', region_name='us-east-2')

# Check the DRS job
job_id = 'drsjob-47be6e4efad090ae3'

try:
    response = drs_client.describe_jobs(filters={'jobIDs': [job_id]})
    
    if response.get('items'):
        job = response['items'][0]
        print(f"Job ID: {job_id}")
        print(f"Status: {job.get('status')}")
        print(f"Type: {job.get('type')}")
        print(f"Created: {job.get('creationDateTime')}")
        print(f"Ended: {job.get('endDateTime')}")
        
        participating_servers = job.get('participatingServers', [])
        print(f"\nParticipating Servers: {len(participating_servers)}")
        
        launched = sum(1 for s in participating_servers if s.get('launchStatus') == 'LAUNCHED')
        print(f"Launched: {launched}")
        
        if participating_servers:
            print(f"\nFirst 3 servers:")
            for i, server in enumerate(participating_servers[:3]):
                print(f"  {i+1}. {server.get('sourceServerID')}")
                print(f"     Launch Status: {server.get('launchStatus')}")
                print(f"     Recovery Instance ID: {server.get('recoveryInstanceID', 'N/A')}")
    else:
        print(f"Job {job_id} not found")
        
except Exception as e:
    print(f"Error: {e}")
