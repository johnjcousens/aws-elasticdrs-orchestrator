#!/usr/bin/env python3
"""
Apply launch configurations to all protection groups.

This script applies launch configurations to all protection groups that don't
have them applied yet. This is needed after the launch-config-preapplication
refactoring to ensure existing protection groups work with the optimized
wave execution.

Usage:
    python3 scripts/apply_launch_configs_to_all_groups.py [--force] [--dry-run]

Options:
    --force     Force re-apply even if status is "ready"
    --dry-run   Show what would be done without making changes
"""

import argparse
import json
import sys
import boto3
from typing import Dict, List


def get_all_protection_groups(region: str) -> List[Dict]:
    """Get all protection groups from DynamoDB."""
    dynamodb = boto3.resource("dynamodb", region_name=region)
    table = dynamodb.Table("hrp-drs-tech-adapter-protection-groups-dev")
    
    response = table.scan()
    groups = response.get("Items", [])
    
    # Handle pagination
    while "LastEvaluatedKey" in response:
        response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
        groups.extend(response.get("Items", []))
    
    return groups


def apply_launch_config(
    group_id: str, 
    force: bool, 
    lambda_client: boto3.client
) -> Dict:
    """Apply launch configuration to a protection group."""
    payload = {
        "operation": "apply_launch_configs",
        "groupId": group_id,
        "force": force
    }
    
    response = lambda_client.invoke(
        FunctionName="hrp-drs-tech-adapter-data-management-handler-dev",
        InvocationType="RequestResponse",
        Payload=json.dumps(payload)
    )
    
    result = json.loads(response["Payload"].read())
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Apply launch configs to all protection groups"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-apply even if status is ready"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--region",
        default="us-east-2",
        help="AWS region (default: us-east-2)"
    )
    
    args = parser.parse_args()
    
    print(f"Fetching protection groups from {args.region}...")
    groups = get_all_protection_groups(args.region)
    
    if not groups:
        print("No protection groups found.")
        return 0
    
    print(f"Found {len(groups)} protection group(s)")
    print()
    
    lambda_client = boto3.client("lambda", region_name=args.region)
    
    results = {
        "success": [],
        "skipped": [],
        "failed": []
    }
    
    for group in groups:
        group_id = group.get("groupId")
        group_name = group.get("name", "Unnamed")
        server_count = len(group.get("sourceServerIds", []))
        
        # Check current launch config status
        launch_config_status = group.get("launchConfigStatus", {})
        current_status = launch_config_status.get("status", "not_configured")
        
        print(f"Processing: {group_name} ({group_id})")
        print(f"  Servers: {server_count}")
        print(f"  Current status: {current_status}")
        
        # Skip if already ready and not forcing
        if current_status == "ready" and not args.force:
            print(f"  ✓ Skipped (already ready)")
            results["skipped"].append({
                "groupId": group_id,
                "name": group_name,
                "reason": "already_ready"
            })
            print()
            continue
        
        if args.dry_run:
            print(f"  [DRY RUN] Would apply launch configs")
            results["success"].append({
                "groupId": group_id,
                "name": group_name,
                "dry_run": True
            })
            print()
            continue
        
        try:
            print(f"  Applying launch configs...")
            result = apply_launch_config(group_id, args.force, lambda_client)
            
            if result.get("statusCode") == 200:
                body = json.loads(result.get("body", "{}"))
                applied = body.get("appliedServers", 0)
                failed = body.get("failedServers", 0)
                
                print(f"  ✓ Success: {applied} applied, {failed} failed")
                results["success"].append({
                    "groupId": group_id,
                    "name": group_name,
                    "applied": applied,
                    "failed": failed
                })
            else:
                error_body = json.loads(result.get("body", "{}"))
                error_msg = error_body.get("message", "Unknown error")
                print(f"  ✗ Failed: {error_msg}")
                results["failed"].append({
                    "groupId": group_id,
                    "name": group_name,
                    "error": error_msg
                })
        
        except Exception as e:
            print(f"  ✗ Error: {e}")
            results["failed"].append({
                "groupId": group_id,
                "name": group_name,
                "error": str(e)
            })
        
        print()
    
    # Print summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total groups: {len(groups)}")
    print(f"Success: {len(results['success'])}")
    print(f"Skipped: {len(results['skipped'])}")
    print(f"Failed: {len(results['failed'])}")
    
    if results["failed"]:
        print()
        print("Failed groups:")
        for item in results["failed"]:
            print(f"  - {item['name']} ({item['groupId']}): {item['error']}")
    
    return 1 if results["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
