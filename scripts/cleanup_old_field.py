#!/usr/bin/env python3
"""
Remove old serverStatuses field from DynamoDB waves.
"""
import boto3
import os

profile = os.environ.get("AWS_PROFILE")
session = boto3.Session(profile_name=profile) if profile else boto3.Session()
dynamodb = session.client("dynamodb")
TABLE_NAME = "aws-drs-orchestration-execution-history-dev"

response = dynamodb.scan(TableName=TABLE_NAME)
items = response["Items"]

print(f"Found {len(items)} executions")

for item in items:
    execution_id = item["executionId"]["S"]
    plan_id = item["planId"]["S"]

    if "waves" not in item or "L" not in item["waves"]:
        continue

    waves = item["waves"]["L"]
    updated = False

    for wave in waves:
        if "M" in wave and "serverStatuses" in wave["M"]:
            del wave["M"]["serverStatuses"]
            updated = True

    if updated:
        dynamodb.update_item(
            TableName=TABLE_NAME,
            Key={"executionId": {"S": execution_id}, "planId": {"S": plan_id}},
            UpdateExpression="SET waves = :waves",
            ExpressionAttributeValues={":waves": {"L": waves}},
        )
        print(f"Cleaned {execution_id}")

print("Done")
