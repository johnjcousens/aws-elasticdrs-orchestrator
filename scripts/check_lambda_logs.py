#!/usr/bin/env python3
"""
Check Lambda logs for the poll operation to see enrichment debug output.
"""
import boto3
import time
from datetime import datetime, timedelta

# Configuration
function_name = "hrp-drs-tech-adapter-execution-handler-dev"
region = "us-east-2"
profile = "AWSAdministratorAccess-891376951562"

# Create CloudWatch Logs client
session = boto3.Session(profile_name=profile, region_name=region)
logs_client = session.client("logs")

log_group = f"/aws/lambda/{function_name}"

# Get logs from last 10 minutes
start_time = int((datetime.now() - timedelta(minutes=10)).timestamp() * 1000)
end_time = int(datetime.now().timestamp() * 1000)

print(f"Fetching logs from {log_group}...")
print(f"Time range: last 10 minutes")
print("="*80)

try:
    # Get log streams
    streams_response = logs_client.describe_log_streams(
        logGroupName=log_group,
        orderBy="LastEventTime",
        descending=True,
        limit=5
    )
    
    for stream in streams_response.get("logStreams", []):
        stream_name = stream["logStreamName"]
        
        # Get events from this stream
        events_response = logs_client.get_log_events(
            logGroupName=log_group,
            logStreamName=stream_name,
            startTime=start_time,
            endTime=end_time,
            limit=100
        )
        
        events = events_response.get("events", [])
        if not events:
            continue
            
        print(f"\nStream: {stream_name}")
        print("-"*80)
        
        for event in events:
            timestamp = datetime.fromtimestamp(event["timestamp"] / 1000)
            message = event["message"].strip()
            
            # Filter for relevant messages
            if any(keyword in message for keyword in [
                "DEBUG:",
                "Enriched",
                "poll",
                "recovery instance",
                "batch_describe_ec2",
                "ERROR",
                "Error"
            ]):
                print(f"[{timestamp.strftime('%H:%M:%S')}] {message}")

except Exception as e:
    print(f"Error fetching logs: {e}")
