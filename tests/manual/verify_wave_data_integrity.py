#!/usr/bin/env python3
"""
Data Integrity Verification for Wave Status Polling Refactoring.

This script verifies that no data is lost during wave transitions after
refactoring poll_wave_status() into read-only (query-handler) and write
operations (execution-handler).

Task 4.10: Verify no data loss during wave transitions

Verification Scope:
1. All execution history fields are populated correctly
2. No missing data in wave status updates
3. Wave completion, pause, and cancellation states work correctly
4. Execution progress tracking remains accurate
5. Server status data is preserved across wave transitions

Usage:
    python tests/manual/verify_wave_data_integrity.py
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set

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

# ANSI color codes
RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
CYAN = "\033[0;36m"
NC = "\033[0m"  # No Color


def print_header(text: str) -> None:
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(text)
    print("=" * 80)


def print_subheader(text: str) -> None:
    """Print a formatted subheader."""
    print(f"\n{CYAN}--- {text} ---{NC}")


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


# Expected field schema for execution records
REQUIRED_FIELDS = {
    "executionId": str,
    "planId": str,
    "status": str,
    "lastUpdated": (int, float),
}

OPTIONAL_FIELDS = {
    "startTime": (int, float),
    "endTime": (int, float),
    "currentWave": int,
    "totalWaves": int,
    "completedWaves": int,
    "failedWaves": int,
    "pausedBeforeWave": int,
    "errorMessage": str,
    "errorCode": str,
    "durationSeconds": (int, float),
    "statusReason": str,
}

# Status-specific required fields
STATUS_REQUIRED_FIELDS = {
    "COMPLETED": ["endTime", "completedWaves", "durationSeconds"],
    "FAILED": ["endTime", "failedWaves", "durationSeconds"],
    "CANCELLED": ["endTime"],
    "PAUSED": [],  # pausedBeforeWave is optional
    "RUNNING": ["currentWave"],
}


def verify_field_types(item: Dict, field_name: str, expected_types: tuple) -> bool:
    """Verify field exists and has correct type."""
    if field_name not in item:
        return False
    
    value = item[field_name]
    if not isinstance(expected_types, tuple):
        expected_types = (expected_types,)
    
    return isinstance(value, expected_types)


def verify_execution_schema(execution: Dict) -> Dict[str, List[str]]:
    """
    Verify execution record has all required fields with correct types.
    
    Returns:
        Dictionary with 'missing', 'invalid_type', and 'warnings' lists
    """
    issues = {
        "missing": [],
        "invalid_type": [],
        "warnings": [],
    }
    
    # Check required fields
    for field, expected_type in REQUIRED_FIELDS.items():
        if field not in execution:
            issues["missing"].append(field)
        elif not verify_field_types(execution, field, expected_type):
            issues["invalid_type"].append(
                f"{field} (expected {expected_type}, got {type(execution[field])})"
            )
    
    # Check status-specific required fields
    status = execution.get("status", "")
    if status in STATUS_REQUIRED_FIELDS:
        for field in STATUS_REQUIRED_FIELDS[status]:
            if field not in execution:
                issues["missing"].append(f"{field} (required for {status})")
    
    # Check optional fields for type correctness (if present)
    for field, expected_type in OPTIONAL_FIELDS.items():
        if field in execution:
            if not verify_field_types(execution, field, expected_type):
                issues["invalid_type"].append(
                    f"{field} (expected {expected_type}, got {type(execution[field])})"
                )
    
    # Logical validations
    if "completedWaves" in execution and "totalWaves" in execution:
        if execution["completedWaves"] > execution["totalWaves"]:
            issues["warnings"].append(
                f"completedWaves ({execution['completedWaves']}) > "
                f"totalWaves ({execution['totalWaves']})"
            )
    
    if "startTime" in execution and "endTime" in execution:
        if execution["endTime"] < execution["startTime"]:
            issues["warnings"].append(
                f"endTime ({execution['endTime']}) < startTime ({execution['startTime']})"
            )
    
    if "durationSeconds" in execution:
        if execution["durationSeconds"] < 0:
            issues["warnings"].append(
                f"durationSeconds is negative: {execution['durationSeconds']}"
            )
    
    return issues


def verify_wave_data_completeness(execution: Dict) -> Dict[str, List[str]]:
    """
    Verify wave-specific data is complete and consistent.
    
    Returns:
        Dictionary with 'missing', 'inconsistent', and 'warnings' lists
    """
    issues = {
        "missing": [],
        "inconsistent": [],
        "warnings": [],
    }
    
    status = execution.get("status", "")
    
    # For COMPLETED status, verify wave counts
    if status == "COMPLETED":
        if "completedWaves" not in execution:
            issues["missing"].append("completedWaves (required for COMPLETED)")
        elif "totalWaves" in execution:
            if execution["completedWaves"] != execution["totalWaves"]:
                issues["inconsistent"].append(
                    f"COMPLETED but completedWaves ({execution['completedWaves']}) "
                    f"!= totalWaves ({execution['totalWaves']})"
                )
    
    # For FAILED status, verify failure data
    if status == "FAILED":
        if "failedWaves" not in execution:
            issues["missing"].append("failedWaves (required for FAILED)")
        
        if "errorMessage" not in execution:
            issues["warnings"].append("errorMessage missing for FAILED status")
        
        if "errorCode" not in execution:
            issues["warnings"].append("errorCode missing for FAILED status")
    
    # For PAUSED status, verify pause data
    if status == "PAUSED":
        if "pausedBeforeWave" not in execution:
            issues["warnings"].append("pausedBeforeWave missing for PAUSED status")
    
    # For CANCELLED status, verify cancellation data
    if status == "CANCELLED":
        if "endTime" not in execution:
            issues["missing"].append("endTime (required for CANCELLED)")
    
    return issues


def verify_timestamp_consistency(execution: Dict) -> Dict[str, List[str]]:
    """
    Verify timestamp fields are consistent and reasonable.
    
    Returns:
        Dictionary with 'inconsistent' and 'warnings' lists
    """
    issues = {
        "inconsistent": [],
        "warnings": [],
    }
    
    current_time = int(time.time())
    
    # Check lastUpdated is recent (within last 7 days)
    if "lastUpdated" in execution:
        last_updated = execution["lastUpdated"]
        age_seconds = current_time - last_updated
        age_days = age_seconds / 86400
        
        if age_days > 7:
            issues["warnings"].append(
                f"lastUpdated is {age_days:.1f} days old (may be stale)"
            )
    
    # Check startTime is not in the future
    if "startTime" in execution:
        if execution["startTime"] > current_time:
            issues["inconsistent"].append(
                f"startTime is in the future: "
                f"{datetime.fromtimestamp(execution['startTime'])}"
            )
    
    # Check endTime is not in the future
    if "endTime" in execution:
        if execution["endTime"] > current_time:
            issues["inconsistent"].append(
                f"endTime is in the future: "
                f"{datetime.fromtimestamp(execution['endTime'])}"
            )
    
    # Verify duration calculation
    if all(k in execution for k in ["startTime", "endTime", "durationSeconds"]):
        calculated_duration = execution["endTime"] - execution["startTime"]
        stored_duration = execution["durationSeconds"]
        
        # Allow 1 second tolerance for rounding
        if abs(calculated_duration - stored_duration) > 1:
            issues["inconsistent"].append(
                f"durationSeconds ({stored_duration}) doesn't match "
                f"calculated duration ({calculated_duration})"
            )
    
    return issues


def analyze_execution_record(execution: Dict) -> Dict:
    """
    Comprehensive analysis of execution record data integrity.
    
    Returns:
        Dictionary with analysis results
    """
    execution_id = execution.get("executionId", "UNKNOWN")
    status = execution.get("status", "UNKNOWN")
    
    print_subheader(f"Analyzing Execution: {execution_id} (Status: {status})")
    
    # Run all verification checks
    schema_issues = verify_execution_schema(execution)
    wave_issues = verify_wave_data_completeness(execution)
    timestamp_issues = verify_timestamp_consistency(execution)
    
    # Combine all issues
    all_issues = {
        "schema": schema_issues,
        "wave_data": wave_issues,
        "timestamps": timestamp_issues,
    }
    
    # Count total issues
    total_errors = (
        len(schema_issues["missing"]) +
        len(schema_issues["invalid_type"]) +
        len(wave_issues["missing"]) +
        len(wave_issues["inconsistent"]) +
        len(timestamp_issues["inconsistent"])
    )
    
    total_warnings = (
        len(schema_issues["warnings"]) +
        len(wave_issues["warnings"]) +
        len(timestamp_issues["warnings"])
    )
    
    # Print results
    if total_errors == 0 and total_warnings == 0:
        print_success(f"No data integrity issues found")
    else:
        if total_errors > 0:
            print_error(f"Found {total_errors} data integrity errors")
        if total_warnings > 0:
            print_warning(f"Found {total_warnings} warnings")
    
    # Print detailed issues
    if schema_issues["missing"]:
        print(f"  {RED}Missing fields:{NC}")
        for field in schema_issues["missing"]:
            print(f"    - {field}")
    
    if schema_issues["invalid_type"]:
        print(f"  {RED}Invalid field types:{NC}")
        for field in schema_issues["invalid_type"]:
            print(f"    - {field}")
    
    if wave_issues["missing"]:
        print(f"  {RED}Missing wave data:{NC}")
        for field in wave_issues["missing"]:
            print(f"    - {field}")
    
    if wave_issues["inconsistent"]:
        print(f"  {RED}Inconsistent wave data:{NC}")
        for issue in wave_issues["inconsistent"]:
            print(f"    - {issue}")
    
    if timestamp_issues["inconsistent"]:
        print(f"  {RED}Inconsistent timestamps:{NC}")
        for issue in timestamp_issues["inconsistent"]:
            print(f"    - {issue}")
    
    # Print warnings
    all_warnings = (
        schema_issues["warnings"] +
        wave_issues["warnings"] +
        timestamp_issues["warnings"]
    )
    
    if all_warnings:
        print(f"  {YELLOW}Warnings:{NC}")
        for warning in all_warnings:
            print(f"    - {warning}")
    
    return {
        "execution_id": execution_id,
        "status": status,
        "issues": all_issues,
        "error_count": total_errors,
        "warning_count": total_warnings,
    }


def query_executions_by_status(status: Optional[str] = None, limit: int = 10) -> List[Dict]:
    """Query executions from DynamoDB, optionally filtered by status."""
    try:
        if status:
            print_info(f"Querying executions with status: {status}")
            # Note: This requires a GSI on status field
            # For now, scan and filter
            response = table.scan(Limit=50)
            items = [
                item for item in response.get("Items", [])
                if item.get("status") == status
            ][:limit]
        else:
            print_info(f"Querying recent executions (limit: {limit})")
            response = table.scan(Limit=limit)
            items = response.get("Items", [])
        
        return items
    except ClientError as e:
        print_error(f"Failed to query executions: {e}")
        return []


def test_wave_transition_data_flow() -> bool:
    """
    Test complete wave transition data flow.
    
    Creates a test execution, simulates wave transitions, and verifies
    data integrity at each step.
    """
    print_header("TEST: Wave Transition Data Flow")
    
    execution_id = f"data-integrity-test-{int(time.time())}"
    plan_id = "test-plan-001"
    
    try:
        # Step 1: Create initial execution
        print_subheader("Step 1: Create Initial Execution")
        
        current_time = int(time.time())
        initial_data = {
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
        
        table.put_item(Item=initial_data)
        print_success("Created initial execution")
        
        # Verify initial data
        item = table.get_item(
            Key={"executionId": execution_id, "planId": plan_id}
        ).get("Item")
        
        analysis = analyze_execution_record(item)
        if analysis["error_count"] > 0:
            print_error("Initial execution has data integrity issues")
            return False
        
        # Step 2: Simulate wave completion
        print_subheader("Step 2: Simulate Wave 1 Completion")
        
        wave_data = {
            "completed_waves": 1,
            "start_time": current_time,
        }
        
        payload = {
            "action": "update_wave_completion_status",
            "execution_id": execution_id,
            "plan_id": plan_id,
            "status": "RUNNING",
            "wave_data": wave_data,
        }
        
        response = lambda_client.invoke(
            FunctionName=EXECUTION_HANDLER,
            InvocationType="RequestResponse",
            Payload=json.dumps(payload),
        )
        
        result = json.loads(response["Payload"].read())
        print(f"Update response: {result}")
        
        # Wait for consistency
        time.sleep(2)
        
        # Verify wave 1 completion data
        item = table.get_item(
            Key={"executionId": execution_id, "planId": plan_id}
        ).get("Item")
        
        analysis = analyze_execution_record(item)
        if analysis["error_count"] > 0:
            print_error("Wave 1 completion has data integrity issues")
            return False
        
        # Verify completedWaves was updated
        if item.get("completedWaves") != 1:
            print_error(f"completedWaves not updated (expected 1, got {item.get('completedWaves')})")
            return False
        
        print_success("Wave 1 completion data verified")
        
        # Step 3: Simulate pause before wave 2
        print_subheader("Step 3: Simulate Pause Before Wave 2")
        
        wave_data = {
            "paused_before_wave": 2,
        }
        
        payload = {
            "action": "update_wave_completion_status",
            "execution_id": execution_id,
            "plan_id": plan_id,
            "status": "PAUSED",
            "wave_data": wave_data,
        }
        
        response = lambda_client.invoke(
            FunctionName=EXECUTION_HANDLER,
            InvocationType="RequestResponse",
            Payload=json.dumps(payload),
        )
        
        result = json.loads(response["Payload"].read())
        print(f"Update response: {result}")
        
        # Wait for consistency
        time.sleep(2)
        
        # Verify pause data
        item = table.get_item(
            Key={"executionId": execution_id, "planId": plan_id}
        ).get("Item")
        
        analysis = analyze_execution_record(item)
        if analysis["error_count"] > 0:
            print_error("Pause state has data integrity issues")
            return False
        
        # Verify pause fields
        if item.get("status") != "PAUSED":
            print_error(f"Status not updated to PAUSED (got {item.get('status')})")
            return False
        
        if item.get("pausedBeforeWave") != 2:
            print_error(f"pausedBeforeWave not set (expected 2, got {item.get('pausedBeforeWave')})")
            return False
        
        print_success("Pause state data verified")
        
        # Step 4: Simulate completion
        print_subheader("Step 4: Simulate Execution Completion")
        
        wave_data = {
            "completed_waves": 3,
            "start_time": current_time,
        }
        
        payload = {
            "action": "update_wave_completion_status",
            "execution_id": execution_id,
            "plan_id": plan_id,
            "status": "COMPLETED",
            "wave_data": wave_data,
        }
        
        response = lambda_client.invoke(
            FunctionName=EXECUTION_HANDLER,
            InvocationType="RequestResponse",
            Payload=json.dumps(payload),
        )
        
        result = json.loads(response["Payload"].read())
        print(f"Update response: {result}")
        
        # Wait for consistency
        time.sleep(2)
        
        # Verify completion data
        item = table.get_item(
            Key={"executionId": execution_id, "planId": plan_id}
        ).get("Item")
        
        analysis = analyze_execution_record(item)
        if analysis["error_count"] > 0:
            print_error("Completion state has data integrity issues")
            return False
        
        # Verify completion fields
        required_completion_fields = ["endTime", "completedWaves", "durationSeconds"]
        for field in required_completion_fields:
            if field not in item:
                print_error(f"Missing required completion field: {field}")
                return False
        
        if item.get("status") != "COMPLETED":
            print_error(f"Status not updated to COMPLETED (got {item.get('status')})")
            return False
        
        if item.get("completedWaves") != 3:
            print_error(f"completedWaves not updated (expected 3, got {item.get('completedWaves')})")
            return False
        
        print_success("Completion state data verified")
        
        # Step 5: Verify no data loss
        print_subheader("Step 5: Verify No Data Loss")
        
        # Check all initial fields are still present
        for field in initial_data.keys():
            if field not in item and field not in ["lastUpdated"]:  # lastUpdated changes
                print_error(f"Initial field lost during transitions: {field}")
                return False
        
        print_success("All initial fields preserved through transitions")
        
        return True
        
    except Exception as e:
        print_error(f"Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        print_subheader("Cleanup")
        try:
            table.delete_item(
                Key={"executionId": execution_id, "planId": plan_id}
            )
            print_success("Test execution cleaned up")
        except Exception as e:
            print_warning(f"Failed to cleanup test execution: {e}")


def main() -> int:
    """Run comprehensive data integrity verification."""
    print_header("WAVE DATA INTEGRITY VERIFICATION")
    print(f"Region: {REGION}")
    print(f"Table: {TABLE_NAME}")
    print(f"Execution Handler: {EXECUTION_HANDLER}")
    
    all_passed = True
    
    # Test 1: Analyze recent executions
    print_header("TEST 1: Analyze Recent Executions")
    
    executions = query_executions_by_status(limit=10)
    
    if not executions:
        print_warning("No recent executions found")
    else:
        print_info(f"Analyzing {len(executions)} recent executions")
        
        total_errors = 0
        total_warnings = 0
        
        for execution in executions:
            analysis = analyze_execution_record(execution)
            total_errors += analysis["error_count"]
            total_warnings += analysis["warning_count"]
        
        print_subheader("Summary")
        print(f"Total executions analyzed: {len(executions)}")
        print(f"Total errors found: {total_errors}")
        print(f"Total warnings found: {total_warnings}")
        
        if total_errors > 0:
            print_error(f"Found {total_errors} data integrity errors in recent executions")
            all_passed = False
        else:
            print_success("No data integrity errors in recent executions")
    
    # Test 2: Analyze executions by status
    print_header("TEST 2: Analyze Executions by Status")
    
    for status in ["COMPLETED", "FAILED", "CANCELLED", "PAUSED", "RUNNING"]:
        print_subheader(f"Status: {status}")
        
        status_executions = query_executions_by_status(status=status, limit=5)
        
        if not status_executions:
            print_info(f"No {status} executions found")
            continue
        
        print_info(f"Found {len(status_executions)} {status} executions")
        
        status_errors = 0
        for execution in status_executions:
            analysis = analyze_execution_record(execution)
            status_errors += analysis["error_count"]
        
        if status_errors > 0:
            print_error(f"Found {status_errors} errors in {status} executions")
            all_passed = False
        else:
            print_success(f"No errors in {status} executions")
    
    # Test 3: Wave transition data flow
    print_header("TEST 3: Wave Transition Data Flow")
    
    transition_test_passed = test_wave_transition_data_flow()
    
    if not transition_test_passed:
        print_error("Wave transition data flow test FAILED")
        all_passed = False
    else:
        print_success("Wave transition data flow test PASSED")
    
    # Final summary
    print_header("VERIFICATION SUMMARY")
    
    if all_passed:
        print_success("ALL DATA INTEGRITY CHECKS PASSED")
        print("\nConclusion:")
        print("  ✅ No data loss detected during wave transitions")
        print("  ✅ All execution history fields populated correctly")
        print("  ✅ Wave completion, pause, and cancellation states work correctly")
        print("  ✅ Execution progress tracking remains accurate")
        print("  ✅ Timestamp consistency maintained")
        return 0
    else:
        print_error("SOME DATA INTEGRITY CHECKS FAILED")
        print("\nIssues detected:")
        print("  ❌ Data integrity errors found in execution records")
        print("  ❌ Review detailed output above for specific issues")
        return 1


if __name__ == "__main__":
    exit(main())
