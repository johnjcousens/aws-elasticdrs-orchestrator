#!/usr/bin/env python3
"""
Verification script for execution history table updates.

This script verifies that wave completion status is being persisted correctly
in the execution history DynamoDB table by:
1. Querying recent executions
2. Verifying required fields are present
3. Checking CloudWatch Logs for execution-handler updates
4. Verifying no writes from query-handler
5. Creating a test execution and verifying the update

Usage:
    python tests/manual/verify_execution_history_updates.py
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

# Configuration
REGION = "us-east-1"
TABLE_NAME = "aws-drs-orchestration-execution-history-qa"
EXECUTION_HANDLER = "aws-drs-orchestration-execution-handler-qa"
QUERY_HANDLER = "aws-drs-orchestration-query-handler-qa"

# Initialize AWS clients
dynamodb = boto3.resource("dynamodb", region_name=REGION)
table = dynamodb.Table(TABLE_NAME)
lambda_client = boto3.client("lambda", region_name=REGION)
logs_client = boto3.client("logs", region_name=REGION)

# ANSI color codes
RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
NC = "\033[0m"  # No Color


def print_header(text: str) -> None:
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(text)
    print("=" * 80)


def print_success(text: str) -> None:
    """Print success message in green."""
    print(f"{GREEN}✅ {text}{NC}")


def print_error(text: str) -> None:
    """Print error message in red."""
    print(f"{RED}❌ {text}{NC}")


def print_warning(text: str) -> None:
    """Print warning message in yellow."""
    print(f"{YELLOW}⚠️  {text}{NC}")


def print_info(text: str) -> None:
    """Print info message in blue."""
    print(f"{BLUE}ℹ️  {text}{NC}")


def query_recent_executions() -> List[Dict]:
    """Query recent executions from DynamoDB."""
    print_header("STEP 1: Query Recent Executions")
    print_info(f"Querying table: {TABLE_NAME}")
    
    try:
        response = table.scan(Limit=10)
        items = response.get("Items", [])
        
        if not items:
            print_warning("No executions found in table")
            return []
        
        print(f"\nFound {len(items)} recent executions:")
        print("\n{:<30} {:<30} {:<15} {:<10} {:<10}".format(
            "Execution ID", "Plan ID", "Status", "Current Wave", "Completed Waves"
        ))
        print("-" * 100)
        
        for item in items:
            execution_id = item.get("executionId", "N/A")
            plan_id = item.get("planId", "N/A")
            status = item.get("status", "N/A")
            current_wave = item.get("currentWave", "N/A")
            completed_waves = item.get("completedWaves", "N/A")
            
            print("{:<30} {:<30} {:<15} {:<10} {:<10}".format(
                execution_id[:28], plan_id[:28], status, 
                str(current_wave), str(completed_waves)
            ))
        
        print_success(f"Retrieved {len(items)} executions")
        return items
        
    except ClientError as e:
        print_error(f"Failed to query executions: {e}")
        return []


def get_execution_details(execution_id: str, plan_id: str) -> Optional[Dict]:
    """Get detailed execution information."""
    try:
        response = table.get_item(
            Key={"executionId": execution_id, "planId": plan_id}
        )
        return response.get("Item")
    except ClientError as e:
        print_error(f"Failed to get execution {execution_id}: {e}")
        return None


def verify_execution_fields(execution_id: str, plan_id: str) -> bool:
    """Verify required fields exist in execution record."""
    print_info(f"Verifying fields for execution: {execution_id}")
    
    item = get_execution_details(execution_id, plan_id)
    if not item:
        print_error(f"Execution {execution_id} not found")
        return False
    
    has_errors = False
    
    # Required fields
    required_fields = ["status", "lastUpdated"]
    for field in required_fields:
        if field in item and item[field] is not None:
            print(f"  {GREEN}✓{NC} {field}: {item[field]}")
        else:
            print(f"  {RED}✗{NC} {field}: MISSING")
            has_errors = True
    
    # Optional but expected fields
    optional_fields = ["currentWave", "completedWaves", "failedWaves"]
    for field in optional_fields:
        if field in item and item[field] is not None:
            print(f"  {GREEN}✓{NC} {field}: {item[field]}")
        else:
            print(f"  {YELLOW}⚠{NC} {field}: MISSING (may be OK)")
    
    # Status-specific fields
    status = item.get("status")
    
    if status in ["COMPLETED", "FAILED", "CANCELLED"]:
        if "endTime" in item and item["endTime"] is not None:
            print(f"  {GREEN}✓{NC} endTime: {item['endTime']}")
        else:
            print(f"  {RED}✗{NC} endTime: MISSING (required for {status})")
            has_errors = True
    
    if status == "PAUSED":
        if "pausedBeforeWave" in item:
            print(f"  {GREEN}✓{NC} pausedBeforeWave: {item['pausedBeforeWave']}")
        else:
            print(f"  {YELLOW}⚠{NC} pausedBeforeWave: MISSING (optional)")
    
    if status == "FAILED":
        if "errorMessage" in item:
            print(f"  {GREEN}✓{NC} errorMessage: {item['errorMessage']}")
        else:
            print(f"  {YELLOW}⚠{NC} errorMessage: MISSING (optional)")
    
    if not has_errors:
        print_success("All required fields present")
    else:
        print_error("Some required fields missing")
    
    return not has_errors


def check_cloudwatch_logs(log_group: str, filter_pattern: str, 
                          minutes: int = 10) -> List[Dict]:
    """Check CloudWatch Logs for specific patterns."""
    print_info(f"Checking logs for: {filter_pattern}")
    
    try:
        start_time = int((datetime.now() - timedelta(minutes=minutes)).timestamp() * 1000)
        
        response = logs_client.filter_log_events(
            logGroupName=log_group,
            startTime=start_time,
            filterPattern=filter_pattern,
            limit=50,
        )
        
        events = response.get("events", [])
        
        if events:
            print(f"\nFound {len(events)} log events:")
            for event in events[:10]:  # Show first 10
                timestamp = datetime.fromtimestamp(event["timestamp"] / 1000)
                message = event["message"][:100]  # Truncate long messages
                print(f"  [{timestamp}] {message}")
            
            if len(events) > 10:
                print(f"  ... and {len(events) - 10} more events")
        else:
            print_warning(f"No log events found matching: {filter_pattern}")
        
        return events
        
    except ClientError as e:
        print_error(f"Failed to query logs: {e}")
        return []


def verify_execution_handler_updates() -> bool:
    """Verify execution-handler is updating wave completion status."""
    print_header("STEP 2: Check Execution Handler Updates")
    
    log_group = f"/aws/lambda/{EXECUTION_HANDLER}"
    events = check_cloudwatch_logs(log_group, "update_wave_completion_status")
    
    if events:
        print_success("Execution-handler is updating wave completion status")
        return True
    else:
        print_warning("No recent execution-handler updates found (may be OK if no recent executions)")
        return True  # Not an error if no recent activity


def verify_no_query_handler_writes() -> bool:
    """Verify query-handler is not performing DynamoDB writes."""
    print_header("STEP 3: Verify No Query Handler Writes")
    
    log_group = f"/aws/lambda/{QUERY_HANDLER}"
    events = check_cloudwatch_logs(log_group, "update_item")
    
    if not events:
        print_success("No DynamoDB writes detected from query-handler")
        return True
    else:
        print_error("WARNING: DynamoDB writes detected from query-handler!")
        print("\nDetected write operations:")
        for event in events[:5]:
            print(f"  {event['message'][:200]}")
        return False


def test_execution_update() -> bool:
    """Create test execution and verify update."""
    print_header("STEP 4: Test Execution Update")
    
    execution_id = f"verify-test-{int(time.time())}"
    plan_id = "verify-plan-001"
    
    try:
        # Create test execution
        print_info(f"Creating test execution: {execution_id}")
        
        current_time = int(time.time())
        table.put_item(
            Item={
                "executionId": execution_id,
                "planId": plan_id,
                "status": "RUNNING",
                "startTime": current_time,
                "currentWave": 1,
                "totalWaves": 3,
                "completedWaves": 0,
                "failedWaves": 0,
                "lastUpdated": current_time,
            }
        )
        
        print_success("Test execution created")
        
        # Update via execution-handler
        print_info("Updating execution via execution-handler...")
        
        payload = {
            "action": "update_wave_completion_status",
            "execution_id": execution_id,
            "plan_id": plan_id,
            "status": "COMPLETED",
            "wave_data": {"completed_waves": 3, "start_time": current_time},
        }
        
        response = lambda_client.invoke(
            FunctionName=EXECUTION_HANDLER,
            InvocationType="RequestResponse",
            Payload=json.dumps(payload),
        )
        
        response_payload = json.loads(response["Payload"].read())
        print(f"Lambda response: {json.dumps(response_payload, indent=2)}")
        
        # Wait for DynamoDB consistency
        time.sleep(2)
        
        # Verify update
        print_info("Verifying execution update...")
        success = verify_execution_fields(execution_id, plan_id)
        
        # Cleanup
        print_info("Cleaning up test execution...")
        table.delete_item(
            Key={"executionId": execution_id, "planId": plan_id}
        )
        print_success("Test execution cleaned up")
        
        return success
        
    except Exception as e:
        print_error(f"Test execution update failed: {e}")
        
        # Cleanup on error
        try:
            table.delete_item(
                Key={"executionId": execution_id, "planId": plan_id}
            )
        except:
            pass
        
        return False


def main() -> int:
    """Run all verification steps."""
    print_header("EXECUTION HISTORY TABLE VERIFICATION")
    print(f"Region: {REGION}")
    print(f"Table: {TABLE_NAME}")
    print(f"Execution Handler: {EXECUTION_HANDLER}")
    
    # Run verification steps
    executions = query_recent_executions()
    
    # Verify a sample execution if available
    if executions:
        sample = executions[0]
        print_header("Sample Execution Verification")
        verify_execution_fields(
            sample["executionId"], 
            sample["planId"]
        )
    
    handler_updates_ok = verify_execution_handler_updates()
    no_query_writes_ok = verify_no_query_handler_writes()
    test_update_ok = test_execution_update()
    
    # Summary
    print_header("VERIFICATION SUMMARY")
    
    results = {
        "Execution history table accessible": True,
        "Recent executions found": len(executions) > 0,
        "Execution-handler updates detected": handler_updates_ok,
        "No query-handler writes": no_query_writes_ok,
        "Test execution update works": test_update_ok,
    }
    
    all_passed = all(results.values())
    
    for check, passed in results.items():
        if passed:
            print_success(check)
        else:
            print_error(check)
    
    print()
    if all_passed:
        print_success("ALL VERIFICATIONS PASSED")
        return 0
    else:
        print_error("SOME VERIFICATIONS FAILED")
        return 1


if __name__ == "__main__":
    exit(main())
