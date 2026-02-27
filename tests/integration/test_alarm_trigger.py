#!/usr/bin/env python3
"""
Test script to trigger AccessDenied alarm by attempting unauthorized operations.

This script intentionally causes AccessDenied errors to verify that:
1. Metric filters capture the errors
2. CloudWatch Alarms trigger correctly
3. SNS notifications are sent
"""

import json
import time
import boto3
from botocore.exceptions import ClientError

# Configuration
REGION = "us-east-2"
QUERY_HANDLER_NAME = "aws-drs-orchestration-query-handler-qa"
ALARM_NAME = "aws-drs-orchestration-query-handler-access-denied-qa"

# Initialize clients
lambda_client = boto3.client("lambda", region_name=REGION)
cloudwatch_client = boto3.client("cloudwatch", region_name=REGION)
logs_client = boto3.client("logs", region_name=REGION)


def invoke_lambda_with_write_operation():
    """
    Invoke Query Handler with a write operation that should fail.
    
    Query Handler should only have read permissions, so attempting
    to write to DynamoDB should cause AccessDenied error.
    
    We'll use a direct invocation with an operation that requires
    write permissions to DynamoDB tables.
    """
    # Try to invoke an operation that would require write access
    # Since Query Handler is read-only, any write attempt should fail
    payload = {
        "operation": "test_write_access",
        "queryParams": {
            "region": "us-east-2",
            "testData": "trigger-alarm-test"
        }
    }
    
    try:
        response = lambda_client.invoke(
            FunctionName=QUERY_HANDLER_NAME,
            InvocationType="RequestResponse",
            Payload=json.dumps(payload)
        )
        
        response_payload = json.loads(response["Payload"].read())
        print(f"Lambda Response Status: {response.get('StatusCode')}")
        print(f"Lambda Response: {json.dumps(response_payload, indent=2)[:500]}...")
        
        return response_payload
    except ClientError as e:
        print(f"Error invoking Lambda: {e}")
        return None


def check_metric_filter():
    """Check if metric filter captured the AccessDenied error."""
    log_group = f"/aws/lambda/{QUERY_HANDLER_NAME}"
    
    # Get recent log streams
    response = logs_client.describe_log_streams(
        logGroupName=log_group,
        orderBy="LastEventTime",
        descending=True,
        limit=5
    )
    
    print(f"\nRecent log streams in {log_group}:")
    for stream in response.get("logStreams", []):
        print(f"  - {stream['logStreamName']} (last event: {stream.get('lastEventTime', 'N/A')})")
    
    # Search for AccessDenied in recent logs
    end_time = int(time.time() * 1000)
    start_time = end_time - (5 * 60 * 1000)  # Last 5 minutes
    
    try:
        response = logs_client.filter_log_events(
            logGroupName=log_group,
            startTime=start_time,
            endTime=end_time,
            filterPattern='[..., msg="*AccessDenied*"]',
            limit=10
        )
        
        events = response.get("events", [])
        print(f"\nFound {len(events)} AccessDenied events in last 5 minutes")
        
        for event in events[:3]:  # Show first 3
            print(f"\nTimestamp: {event['timestamp']}")
            print(f"Message: {event['message'][:200]}...")
        
        return len(events) > 0
    except ClientError as e:
        print(f"Error filtering logs: {e}")
        return False


def check_alarm_state():
    """Check the current state of the CloudWatch Alarm."""
    try:
        response = cloudwatch_client.describe_alarms(
            AlarmNames=[ALARM_NAME]
        )
        
        if response["MetricAlarms"]:
            alarm = response["MetricAlarms"][0]
            print(f"\nAlarm State:")
            print(f"  Name: {alarm['AlarmName']}")
            print(f"  State: {alarm['StateValue']}")
            print(f"  State Reason: {alarm.get('StateReason', 'N/A')}")
            print(f"  State Updated: {alarm.get('StateUpdatedTimestamp', 'N/A')}")
            
            return alarm["StateValue"]
        else:
            print(f"Alarm {ALARM_NAME} not found")
            return None
    except ClientError as e:
        print(f"Error describing alarm: {e}")
        return None


def get_metric_statistics():
    """Get recent metric statistics for AccessDeniedErrors."""
    end_time = time.time()
    start_time = end_time - (10 * 60)  # Last 10 minutes
    
    try:
        response = cloudwatch_client.get_metric_statistics(
            Namespace="AWS/Lambda",
            MetricName="AccessDeniedErrors",
            Dimensions=[
                {
                    "Name": "FunctionName",
                    "Value": QUERY_HANDLER_NAME
                }
            ],
            StartTime=int(start_time),
            EndTime=int(end_time),
            Period=60,  # 1 minute periods
            Statistics=["Sum"]
        )
        
        datapoints = sorted(response.get("Datapoints", []), key=lambda x: x["Timestamp"])
        
        print(f"\nMetric Statistics (last 10 minutes):")
        if datapoints:
            for dp in datapoints[-5:]:  # Show last 5 datapoints
                print(f"  {dp['Timestamp']}: {dp['Sum']} errors")
        else:
            print("  No datapoints found")
        
        return datapoints
    except ClientError as e:
        print(f"Error getting metric statistics: {e}")
        return []


def main():
    """Main test execution."""
    print("=" * 80)
    print("CloudWatch Alarm Trigger Test")
    print("=" * 80)
    
    # Step 1: Check initial alarm state
    print("\n[Step 1] Checking initial alarm state...")
    initial_state = check_alarm_state()
    
    # Step 2: Trigger multiple AccessDenied errors (need 5+ to trigger alarm)
    print("\n[Step 2] Triggering AccessDenied errors (need 5+ in 5 minutes)...")
    for i in range(6):
        print(f"\nAttempt {i+1}/6:")
        invoke_lambda_with_write_operation()
        time.sleep(2)  # Small delay between invocations
    
    # Step 3: Wait for logs to be processed
    print("\n[Step 3] Waiting 30 seconds for logs to be processed...")
    time.sleep(30)
    
    # Step 4: Check metric filter captured errors
    print("\n[Step 4] Checking if metric filter captured errors...")
    metric_filter_working = check_metric_filter()
    
    # Step 5: Check metric statistics
    print("\n[Step 5] Checking metric statistics...")
    get_metric_statistics()
    
    # Step 6: Wait for alarm evaluation
    print("\n[Step 6] Waiting 60 seconds for alarm evaluation...")
    time.sleep(60)
    
    # Step 7: Check final alarm state
    print("\n[Step 7] Checking final alarm state...")
    final_state = check_alarm_state()
    
    # Summary
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    print(f"Initial Alarm State: {initial_state}")
    print(f"Metric Filter Working: {metric_filter_working}")
    print(f"Final Alarm State: {final_state}")
    
    if final_state == "ALARM":
        print("\n✓ SUCCESS: Alarm triggered correctly!")
        print("  - Check your email/SNS subscription for notification")
    elif final_state == "OK":
        print("\n⚠ WARNING: Alarm still in OK state")
        print("  - May need more time for evaluation")
        print("  - Check metric statistics to verify errors were recorded")
    else:
        print(f"\n✗ ERROR: Unexpected alarm state: {final_state}")
    
    print("\nNote: It may take a few minutes for the alarm to transition to ALARM state.")
    print("You can monitor the alarm in the CloudWatch console:")
    print(f"https://console.aws.amazon.com/cloudwatch/home?region={REGION}#alarmsV2:alarm/{ALARM_NAME}")


if __name__ == "__main__":
    main()
