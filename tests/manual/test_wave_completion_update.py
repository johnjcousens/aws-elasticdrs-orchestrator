#!/usr/bin/env python3
"""
Manual test script for update_wave_completion_status() function.

This script tests the wave completion update functionality by:
1. Creating test execution records in DynamoDB
2. Invoking execution-handler Lambda with various status types
3. Verifying DynamoDB updates are correct
4. Cleaning up test data

Usage:
    python tests/manual/test_wave_completion_update.py
"""

import json
import time
import boto3
from decimal import Decimal

# Configuration
REGION = "us-east-1"
LAMBDA_FUNCTION_NAME = "aws-drs-orchestration-execution-handler-qa"
DYNAMODB_TABLE_NAME = "aws-drs-orchestration-execution-history-qa"

# Initialize AWS clients
lambda_client = boto3.client("lambda", region_name=REGION)
dynamodb = boto3.resource("dynamodb", region_name=REGION)
table = dynamodb.Table(DYNAMODB_TABLE_NAME)


def create_test_execution(execution_id: str, plan_id: str) -> None:
    """Create a test execution record in DynamoDB."""
    print(f"\n📝 Creating test execution: {execution_id}")
    
    item = {
        "executionId": execution_id,
        "planId": plan_id,
        "status": "RUNNING",
        "startTime": int(time.time()),
        "currentWave": 1,
        "totalWaves": 3,
        "completedWaves": 0,
        "failedWaves": 0,
        "lastUpdated": int(time.time()),
    }
    
    table.put_item(Item=item)
    print(f"✅ Created test execution: {execution_id}")


def invoke_lambda(action: str, payload: dict) -> dict:
    """Invoke execution-handler Lambda function."""
    print(f"\n🚀 Invoking Lambda with action: {action}")
    print(f"   Payload: {json.dumps(payload, indent=2)}")
    
    response = lambda_client.invoke(
        FunctionName=LAMBDA_FUNCTION_NAME,
        InvocationType="RequestResponse",
        Payload=json.dumps(payload),
    )
    
    response_payload = json.loads(response["Payload"].read())
    print(f"   Response: {json.dumps(response_payload, indent=2)}")
    
    return response_payload


def get_execution(execution_id: str, plan_id: str) -> dict:
    """Get execution record from DynamoDB."""
    response = table.get_item(
        Key={"executionId": execution_id, "planId": plan_id}
    )
    return response.get("Item", {})


def verify_execution_status(
    execution_id: str,
    plan_id: str,
    expected_status: str,
    expected_fields: dict = None,
) -> bool:
    """Verify execution status and fields in DynamoDB."""
    print(f"\n🔍 Verifying execution {execution_id} status...")
    
    item = get_execution(execution_id, plan_id)
    
    if not item:
        print(f"❌ Execution {execution_id} not found in DynamoDB")
        return False
    
    # Check status
    actual_status = item.get("status")
    if actual_status != expected_status:
        print(f"❌ Status mismatch: expected {expected_status}, got {actual_status}")
        return False
    
    print(f"✅ Status correct: {actual_status}")
    
    # Check expected fields
    if expected_fields:
        for field, expected_value in expected_fields.items():
            actual_value = item.get(field)
            if actual_value != expected_value:
                print(f"❌ Field {field} mismatch: expected {expected_value}, got {actual_value}")
                return False
            print(f"✅ Field {field} correct: {actual_value}")
    
    # Print full item for inspection
    print(f"\n📋 Full execution record:")
    print(json.dumps(item, indent=2, default=str))
    
    return True


def cleanup_test_execution(execution_id: str, plan_id: str) -> None:
    """Delete test execution record from DynamoDB."""
    print(f"\n🧹 Cleaning up test execution: {execution_id}")
    
    table.delete_item(
        Key={"executionId": execution_id, "planId": plan_id}
    )
    
    print(f"✅ Deleted test execution: {execution_id}")


def test_cancelled_status():
    """Test CANCELLED status update."""
    print("\n" + "=" * 80)
    print("TEST 1: CANCELLED Status")
    print("=" * 80)
    
    execution_id = "test-exec-cancelled-001"
    plan_id = "test-plan-001"
    
    try:
        # Create test execution
        create_test_execution(execution_id, plan_id)
        
        # Invoke Lambda to update status to CANCELLED
        payload = {
            "action": "update_wave_completion_status",
            "execution_id": execution_id,
            "plan_id": plan_id,
            "status": "CANCELLED",
        }
        
        response = invoke_lambda("update_wave_completion_status", payload)
        
        # Verify response
        assert response.get("statusCode") == 200, f"Expected 200, got {response.get('statusCode')}"
        
        # Verify DynamoDB update
        time.sleep(1)  # Wait for DynamoDB consistency
        assert verify_execution_status(
            execution_id,
            plan_id,
            "CANCELLED",
            expected_fields={"endTime": lambda x: x is not None},
        )
        
        print("\n✅ TEST 1 PASSED: CANCELLED status update works correctly")
        
    finally:
        cleanup_test_execution(execution_id, plan_id)


def test_paused_status():
    """Test PAUSED status update."""
    print("\n" + "=" * 80)
    print("TEST 2: PAUSED Status")
    print("=" * 80)
    
    execution_id = "test-exec-paused-001"
    plan_id = "test-plan-001"
    
    try:
        # Create test execution
        create_test_execution(execution_id, plan_id)
        
        # Invoke Lambda to update status to PAUSED
        payload = {
            "action": "update_wave_completion_status",
            "execution_id": execution_id,
            "plan_id": plan_id,
            "status": "PAUSED",
            "wave_data": {
                "paused_before_wave": 2,
            },
        }
        
        response = invoke_lambda("update_wave_completion_status", payload)
        
        # Verify response
        assert response.get("statusCode") == 200, f"Expected 200, got {response.get('statusCode')}"
        
        # Verify DynamoDB update
        time.sleep(1)  # Wait for DynamoDB consistency
        assert verify_execution_status(
            execution_id,
            plan_id,
            "PAUSED",
            expected_fields={"pausedBeforeWave": 2},
        )
        
        print("\n✅ TEST 2 PASSED: PAUSED status update works correctly")
        
    finally:
        cleanup_test_execution(execution_id, plan_id)


def test_completed_status():
    """Test COMPLETED status update."""
    print("\n" + "=" * 80)
    print("TEST 3: COMPLETED Status")
    print("=" * 80)
    
    execution_id = "test-exec-completed-001"
    plan_id = "test-plan-001"
    
    try:
        # Create test execution
        create_test_execution(execution_id, plan_id)
        
        # Get start time for duration calculation
        item = get_execution(execution_id, plan_id)
        start_time = item["startTime"]
        
        # Invoke Lambda to update status to COMPLETED
        payload = {
            "action": "update_wave_completion_status",
            "execution_id": execution_id,
            "plan_id": plan_id,
            "status": "COMPLETED",
            "wave_data": {
                "completed_waves": 3,
                "start_time": start_time,
            },
        }
        
        response = invoke_lambda("update_wave_completion_status", payload)
        
        # Verify response
        assert response.get("statusCode") == 200, f"Expected 200, got {response.get('statusCode')}"
        
        # Verify DynamoDB update
        time.sleep(1)  # Wait for DynamoDB consistency
        assert verify_execution_status(
            execution_id,
            plan_id,
            "COMPLETED",
            expected_fields={
                "endTime": lambda x: x is not None,
                "completedWaves": 3,
                "durationSeconds": lambda x: x is not None and x > 0,
            },
        )
        
        print("\n✅ TEST 3 PASSED: COMPLETED status update works correctly")
        
    finally:
        cleanup_test_execution(execution_id, plan_id)


def test_failed_status():
    """Test FAILED status update."""
    print("\n" + "=" * 80)
    print("TEST 4: FAILED Status")
    print("=" * 80)
    
    execution_id = "test-exec-failed-001"
    plan_id = "test-plan-001"
    
    try:
        # Create test execution
        create_test_execution(execution_id, plan_id)
        
        # Get start time for duration calculation
        item = get_execution(execution_id, plan_id)
        start_time = item["startTime"]
        
        # Invoke Lambda to update status to FAILED
        payload = {
            "action": "update_wave_completion_status",
            "execution_id": execution_id,
            "plan_id": plan_id,
            "status": "FAILED",
            "wave_data": {
                "error": "DRS job failed: LaunchFailed",
                "error_code": "LAUNCH_FAILED",
                "failed_waves": 1,
                "start_time": start_time,
            },
        }
        
        response = invoke_lambda("update_wave_completion_status", payload)
        
        # Verify response
        assert response.get("statusCode") == 200, f"Expected 200, got {response.get('statusCode')}"
        
        # Verify DynamoDB update
        time.sleep(1)  # Wait for DynamoDB consistency
        assert verify_execution_status(
            execution_id,
            plan_id,
            "FAILED",
            expected_fields={
                "endTime": lambda x: x is not None,
                "errorMessage": "DRS job failed: LaunchFailed",
                "errorCode": "LAUNCH_FAILED",
                "failedWaves": 1,
                "durationSeconds": lambda x: x is not None and x > 0,
            },
        )
        
        print("\n✅ TEST 4 PASSED: FAILED status update works correctly")
        
    finally:
        cleanup_test_execution(execution_id, plan_id)


def test_nonexistent_execution():
    """Test updating a non-existent execution."""
    print("\n" + "=" * 80)
    print("TEST 5: Non-Existent Execution")
    print("=" * 80)
    
    execution_id = "test-exec-nonexistent-001"
    plan_id = "test-plan-001"
    
    # Invoke Lambda to update non-existent execution
    payload = {
        "action": "update_wave_completion_status",
        "execution_id": execution_id,
        "plan_id": plan_id,
        "status": "COMPLETED",
    }
    
    response = invoke_lambda("update_wave_completion_status", payload)
    
    # Verify response
    assert response.get("statusCode") == 404, f"Expected 404, got {response.get('statusCode')}"
    assert "not found" in response.get("error", "").lower()
    
    print("\n✅ TEST 5 PASSED: Non-existent execution handled correctly")


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("WAVE COMPLETION STATUS UPDATE TESTS")
    print("=" * 80)
    print(f"Region: {REGION}")
    print(f"Lambda Function: {LAMBDA_FUNCTION_NAME}")
    print(f"DynamoDB Table: {DYNAMODB_TABLE_NAME}")
    
    try:
        test_cancelled_status()
        test_paused_status()
        test_completed_status()
        test_failed_status()
        test_nonexistent_execution()
        
        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
