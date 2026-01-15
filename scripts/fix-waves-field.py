#!/usr/bin/env python3
"""
Fix Waves (PascalCase) to waves (camelCase) in execution history table.
Quick migration script for existing test data.
"""

import boto3
import sys

REGION = "us-east-1"
TABLE_NAME = "aws-elasticdrs-orchestrator-execution-history-test"

dynamodb = boto3.resource("dynamodb", region_name=REGION)
table = dynamodb.Table(TABLE_NAME)


def fix_execution_waves():
    """Scan execution history and fix Waves -> waves."""
    print(f"Scanning {TABLE_NAME} for Waves field...")
    
    response = table.scan(
        FilterExpression="attribute_exists(Waves)"
    )
    
    items = response.get("Items", [])
    print(f"Found {len(items)} executions with Waves (PascalCase)")
    
    if not items:
        print("✅ No items to fix")
        return
    
    for item in items:
        execution_id = item["executionId"]
        plan_id = item["planId"]
        waves_data = item.get("Waves", [])
        
        print(f"Fixing {execution_id}...")
        
        # Update: set waves (camelCase) and remove Waves (PascalCase)
        table.update_item(
            Key={"executionId": execution_id, "planId": plan_id},
            UpdateExpression="SET waves = :waves REMOVE Waves",
            ExpressionAttributeValues={":waves": waves_data}
        )
        
        print(f"  ✅ Fixed {execution_id}")
    
    print(f"\n✅ Fixed {len(items)} executions")


if __name__ == "__main__":
    try:
        fix_execution_waves()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
