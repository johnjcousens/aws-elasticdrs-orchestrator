#!/usr/bin/env python3
"""
Local test for regional capacity calculation.
Run this to test the Lambda logic without deploying.
"""

import json
import sys
import os

# Add lambda directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../lambda"))

from query_handler.index import lambda_handler


def test_regional_capacity():
    """Test the regional capacity calculation with mock data."""

    # Mock event
    event = {
        "httpMethod": "GET",
        "path": "/accounts/capacity/all",
        "headers": {},
        "requestContext": {"authorizer": {"claims": {"sub": "test-user", "email": "test@example.com"}}},
    }

    # Mock context
    class MockContext:
        function_name = "test-function"
        memory_limit_in_mb = 512
        invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test"
        aws_request_id = "test-request-id"

    context = MockContext()

    # Call the handler
    response = lambda_handler(event, context)

    # Parse response
    body = json.loads(response["body"])

    print("=" * 80)
    print("REGIONAL CAPACITY TEST RESULTS")
    print("=" * 80)

    # Print combined capacity
    combined = body.get("combined", {})
    print(f"\nCombined Total:")
    print(f"  Replicating: {combined.get('totalReplicating')} / {combined.get('maxReplicating')}")
    print(f"  Percent: {combined.get('percentUsed'):.1f}%")

    # Print regional capacity
    regional = body.get("regionalCapacity", [])
    print(f"\nRegional Breakdown ({len(regional)} regions):")
    for region in regional:
        print(f"\n  {region['region']}:")
        print(
            f"    Replication: {region['replicatingServers']} / {region['maxReplicating']} ({region['accountCount']} accounts)"
        )
        print(f"    Recovery: {region['recoveryServers']} / {region['recoveryMax']}")
        print(f"    Replication %: {region['replicationPercent']:.1f}%")
        print(f"    Recovery %: {region['recoveryPercent']:.2f}%")

    # Print recovery capacity
    recovery = body.get("recoveryCapacity", {})
    print(f"\nRecovery Capacity:")
    print(f"  Current: {recovery.get('currentServers')} / {recovery.get('maxRecoveryInstances')}")
    print(f"  Percent: {recovery.get('percentUsed'):.2f}%")

    print("\n" + "=" * 80)

    # Validate expectations
    print("\nVALIDATION:")

    # Check us-east-1
    us_east_1 = next((r for r in regional if r["region"] == "us-east-1"), None)
    if us_east_1:
        expected_accounts = 2  # Target + 1 staging with servers
        actual_accounts = us_east_1["accountCount"]
        status = "✓" if actual_accounts == expected_accounts else "✗"
        print(f"{status} us-east-1 account count: {actual_accounts} (expected {expected_accounts})")

        expected_replicating = 12
        actual_replicating = us_east_1["replicatingServers"]
        status = "✓" if actual_replicating == expected_replicating else "✗"
        print(f"{status} us-east-1 replicating: {actual_replicating} (expected {expected_replicating})")

        expected_recovery = 6  # Only target account servers
        actual_recovery = us_east_1["recoveryServers"]
        status = "✓" if actual_recovery == expected_recovery else "✗"
        print(f"{status} us-east-1 recovery: {actual_recovery} (expected {expected_recovery})")

    # Check us-west-2
    us_west_2 = next((r for r in regional if r["region"] == "us-west-2"), None)
    if us_west_2:
        expected_recovery = 0  # All servers are STOPPED
        actual_recovery = us_west_2["recoveryServers"]
        status = "✓" if actual_recovery == expected_recovery else "✗"
        print(f"{status} us-west-2 recovery: {actual_recovery} (expected {expected_recovery})")

    print("\n" + "=" * 80)

    return response


if __name__ == "__main__":
    test_regional_capacity()
