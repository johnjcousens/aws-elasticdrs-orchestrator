#!/usr/bin/env python3
"""
Manual CloudWatch Alarm Trigger Test

This script manually publishes AccessDenied metric data to CloudWatch
to verify that alarms trigger correctly and SNS notifications are sent.

This is a simpler approach than trying to cause actual AccessDenied errors,
and directly tests the alarm configuration.
"""

import time
from datetime import datetime

import boto3

# Configuration
REGION = "us-east-2"
NAMESPACE = "AWS/Lambda"
METRIC_NAME = "AccessDeniedErrors"
FUNCTION_NAME = "aws-drs-orchestration-query-handler-qa"
ALARM_NAME = "aws-drs-orchestration-query-handler-access-denied-qa"

# Initialize clients
cloudwatch_client = boto3.client("cloudwatch", region_name=REGION)


def publish_metric_data(count: int):
    """
    Publish AccessDenied metric data to CloudWatch.
    
    Args:
        count: Number of errors to report
    """
    try:
        response = cloudwatch_client.put_metric_data(
            Namespace=NAMESPACE,
            MetricData=[
                {
                    "MetricName": METRIC_NAME,
                    "Dimensions": [{"Name": "FunctionName", "Value": FUNCTION_NAME}],
                    "Value": count,
                    "Unit": "Count",
                    "Timestamp": datetime.utcnow(),
                }
            ],
        )
        print(f"Published metric: {METRIC_NAME} = {count} for {FUNCTION_NAME}")
        return response
    except Exception as e:
        print(f"Error publishing metric: {e}")
        return None


def check_alarm_state():
    """Check the current state of the CloudWatch Alarm."""
    try:
        response = cloudwatch_client.describe_alarms(AlarmNames=[ALARM_NAME])

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
    except Exception as e:
        print(f"Error describing alarm: {e}")
        return None


def get_metric_statistics():
    """Get recent metric statistics for AccessDeniedErrors."""
    end_time = datetime.utcnow()
    start_time = datetime.utcfromtimestamp(end_time.timestamp() - (10 * 60))

    try:
        response = cloudwatch_client.get_metric_statistics(
            Namespace=NAMESPACE,
            MetricName=METRIC_NAME,
            Dimensions=[{"Name": "FunctionName", "Value": FUNCTION_NAME}],
            StartTime=start_time,
            EndTime=end_time,
            Period=60,
            Statistics=["Sum"],
        )

        datapoints = sorted(response.get("Datapoints", []), key=lambda x: x["Timestamp"])

        print(f"\nMetric Statistics (last 10 minutes):")
        if datapoints:
            for dp in datapoints[-5:]:
                print(f"  {dp['Timestamp']}: {dp['Sum']} errors")
        else:
            print("  No datapoints found")

        return datapoints
    except Exception as e:
        print(f"Error getting metric statistics: {e}")
        return []


def main():
    """Main test execution."""
    print("=" * 80)
    print("CloudWatch Alarm Manual Trigger Test")
    print("=" * 80)

    # Step 1: Check initial alarm state
    print("\n[Step 1] Checking initial alarm state...")
    initial_state = check_alarm_state()

    # Step 2: Publish metric data to trigger alarm (threshold is 5)
    print("\n[Step 2] Publishing metric data to trigger alarm (threshold: 5)...")
    print("Publishing 6 errors to exceed threshold...")
    publish_metric_data(6)

    # Step 3: Wait for metric to be processed
    print("\n[Step 3] Waiting 30 seconds for metric to be processed...")
    time.sleep(30)

    # Step 4: Check metric statistics
    print("\n[Step 4] Checking metric statistics...")
    get_metric_statistics()

    # Step 5: Wait for alarm evaluation (alarms evaluate every 60 seconds)
    print("\n[Step 5] Waiting 90 seconds for alarm evaluation...")
    time.sleep(90)

    # Step 6: Check final alarm state
    print("\n[Step 6] Checking final alarm state...")
    final_state = check_alarm_state()

    # Summary
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    print(f"Initial Alarm State: {initial_state}")
    print(f"Metric Published: 6 errors (threshold: 5)")
    print(f"Final Alarm State: {final_state}")

    if final_state == "ALARM":
        print("\n✓ SUCCESS: Alarm triggered correctly!")
        print("  - Metric data exceeded threshold (6 > 5)")
        print("  - Alarm transitioned to ALARM state")
        print("  - Check your email/SNS subscription for notification")
    elif final_state == "OK":
        print("\n⚠ WARNING: Alarm still in OK state")
        print("  - May need more time for evaluation")
        print("  - Alarm evaluation period is 5 minutes")
        print("  - Check metric statistics to verify data was recorded")
    else:
        print(f"\n✗ ERROR: Unexpected alarm state: {final_state}")

    print("\nNote: CloudWatch alarms evaluate every 60 seconds.")
    print("If alarm hasn't triggered yet, wait a few more minutes and check again.")
    print(f"\nMonitor alarm in CloudWatch console:")
    print(f"https://console.aws.amazon.com/cloudwatch/home?region={REGION}#alarmsV2:alarm/{ALARM_NAME}")


if __name__ == "__main__":
    main()
