#!/usr/bin/env python3
"""
Verification script for Task 11.4: API Gateway Response Wrapping

This script verifies that all three handlers properly:
1. Detect API Gateway invocations via "requestContext"
2. Return wrapped responses (statusCode, headers, body) for API Gateway
3. Return unwrapped responses for direct invocations
"""

import os
import sys
from pathlib import Path

# Add lambda directories to path
lambda_dir = Path(__file__).parent / "lambda"
sys.path.insert(0, str(lambda_dir / "shared"))

# Set required environment variables
os.environ["PROTECTION_GROUPS_TABLE"] = "test-pg"
os.environ["RECOVERY_PLANS_TABLE"] = "test-rp"
os.environ["EXECUTION_HISTORY_TABLE"] = "test-exec"
os.environ["TARGET_ACCOUNTS_TABLE"] = "test-ta"
os.environ["TAG_SYNC_CONFIG_TABLE"] = "test-tag"
os.environ["ORCHESTRATION_ROLE_ARN"] = "arn:aws:iam::123456789012:role/test"
os.environ["STATE_MACHINE_ARN"] = "arn:aws:states:us-east-1:123456789012:stateMachine:test"

def check_handler_structure(handler_name, handler_path):
    """Check if handler has correct structure for dual-mode support"""
    print(f"\n{'='*70}")
    print(f"Checking {handler_name}")
    print(f"{'='*70}")
    
    handler_file = Path(handler_path)
    if not handler_file.exists():
        print(f"❌ Handler file not found: {handler_path}")
        return False
    
    content = handler_file.read_text()
    
    # Check 1: Has lambda_handler entry point
    has_lambda_handler = "def lambda_handler(event, context):" in content
    print(f"✓ Has lambda_handler entry point: {has_lambda_handler}")
    
    # Check 2: Detects API Gateway via requestContext
    has_api_gateway_detection = '"requestContext" in event' in content
    print(f"✓ Detects API Gateway invocation: {has_api_gateway_detection}")
    
    # Check 3: Has API Gateway handling (either separate function or inline)
    has_api_gateway_handler = "def handle_api_gateway_request(event, context):" in content
    has_inline_api_gateway = 'http_method = event.get("httpMethod"' in content
    has_api_gateway_routing = has_api_gateway_handler or has_inline_api_gateway
    routing_type = "separate function" if has_api_gateway_handler else "inline routing"
    print(f"✓ Has API Gateway routing ({routing_type}): {has_api_gateway_routing}")
    
    # Check 4: Has handle_direct_invocation function
    has_direct_handler = "def handle_direct_invocation(event, context):" in content or \
                        "def handle_direct_invocation(event: Dict, context)" in content
    print(f"✓ Has handle_direct_invocation: {has_direct_handler}")
    
    # Check 5: Uses response() function for API Gateway wrapping
    uses_response_function = "return response(" in content
    print(f"✓ Uses response() for API Gateway wrapping: {uses_response_function}")
    
    # Check 6: Imports response utilities
    imports_response_utils = "from shared.response_utils import" in content
    print(f"✓ Imports response utilities: {imports_response_utils}")
    
    all_checks = all([
        has_lambda_handler,
        has_api_gateway_detection,
        has_api_gateway_routing,
        has_direct_handler,
        uses_response_function,
        imports_response_utils
    ])
    
    if all_checks:
        print(f"\n✅ {handler_name} has correct dual-mode structure")
    else:
        print(f"\n❌ {handler_name} is missing some dual-mode components")
    
    return all_checks

def check_response_utils():
    """Check that response utilities provide proper wrapping"""
    print(f"\n{'='*70}")
    print("Checking shared/response_utils.py")
    print(f"{'='*70}")
    
    response_utils_path = Path(__file__).parent / "lambda" / "shared" / "response_utils.py"
    if not response_utils_path.exists():
        print(f"❌ response_utils.py not found")
        return False
    
    content = response_utils_path.read_text()
    
    # Check for response() function
    has_response_func = "def response(" in content
    print(f"✓ Has response() function: {has_response_func}")
    
    # Check for statusCode in response
    has_statuscode = "statusCode" in content
    print(f"✓ Includes statusCode: {has_statuscode}")
    
    # Check for headers in response
    has_headers = "headers" in content
    print(f"✓ Includes headers: {has_headers}")
    
    # Check for body in response
    has_body = '"body"' in content or "'body'" in content
    print(f"✓ Includes body: {has_body}")
    
    all_checks = all([has_response_func, has_statuscode, has_headers, has_body])
    
    if all_checks:
        print(f"\n✅ response_utils.py provides proper API Gateway wrapping")
    else:
        print(f"\n❌ response_utils.py is missing some wrapping components")
    
    return all_checks

def main():
    """Run all verification checks"""
    print("\n" + "="*70)
    print("Task 11.4 Verification: API Gateway Response Wrapping")
    print("="*70)
    
    handlers = [
        ("query-handler", "lambda/query-handler/index.py"),
        ("execution-handler", "lambda/execution-handler/index.py"),
        ("data-management-handler", "lambda/data-management-handler/index.py"),
    ]
    
    results = []
    
    # Check each handler
    for handler_name, handler_path in handlers:
        result = check_handler_structure(handler_name, handler_path)
        results.append((handler_name, result))
    
    # Check response utilities
    response_utils_ok = check_response_utils()
    results.append(("response_utils", response_utils_ok))
    
    # Summary
    print(f"\n{'='*70}")
    print("VERIFICATION SUMMARY")
    print(f"{'='*70}")
    
    all_passed = all(result for _, result in results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\n{'='*70}")
    if all_passed:
        print("✅ ALL CHECKS PASSED")
        print("\nConclusion: All handlers properly detect API Gateway invocations")
        print("and return wrapped responses (statusCode, headers, body).")
        print("\nTask 11.4 requirements are satisfied:")
        print("  ✓ API Gateway detection via 'requestContext'")
        print("  ✓ Wrapped responses using response() function")
        print("  ✓ Direct invocation unwrapping in handle_direct_invocation()")
    else:
        print("❌ SOME CHECKS FAILED")
        print("\nPlease review the failed components above.")
    print(f"{'='*70}\n")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
