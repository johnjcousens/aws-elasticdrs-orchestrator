#!/usr/bin/env python3
"""
DRS Conflict Resolution Script

Identifies and terminates conflicting DRS jobs that prevent new executions.
This resolves the ConflictException that causes Step Functions to fail.

Usage:
    python3 scripts/cleanup-drs-conflicts.py --region us-west-2 [--dry-run]
"""

import argparse
import boto3
import json
import sys
from datetime import datetime, timezone
from typing import Dict, List, Any


def get_active_drs_jobs(region: str) -> List[Dict[str, Any]]:
    """Get all active DRS jobs in the region."""
    drs_client = boto3.client('drs', region_name=region)
    
    try:
        response = drs_client.describe_jobs()
        jobs = response.get('items', [])
        
        # Filter to active jobs (not completed/failed)
        active_jobs = []
        for job in jobs:
            status = job.get('status', 'UNKNOWN')
            if status not in ['COMPLETED', 'FAILED']:
                active_jobs.append(job)
        
        return active_jobs
    except Exception as e:
        print(f"Error getting DRS jobs: {e}")
        return []


def get_recovery_instances(region: str) -> List[Dict[str, Any]]:
    """Get all recovery instances in the region."""
    drs_client = boto3.client('drs', region_name=region)
    
    try:
        response = drs_client.describe_recovery_instances()
        return response.get('items', [])
    except Exception as e:
        print(f"Error getting recovery instances: {e}")
        return []


def terminate_recovery_instances(region: str, instance_ids: List[str], dry_run: bool = False) -> bool:
    """Terminate recovery instances to resolve conflicts."""
    if not instance_ids:
        return True
    
    drs_client = boto3.client('drs', region_name=region)
    
    print(f"{'[DRY RUN] ' if dry_run else ''}Terminating {len(instance_ids)} recovery instances...")
    for instance_id in instance_ids:
        print(f"  - {instance_id}")
    
    if dry_run:
        return True
    
    try:
        response = drs_client.terminate_recovery_instances(
            recoveryInstanceIDs=instance_ids
        )
        
        job = response.get('job', {})
        job_id = job.get('jobID')
        
        print(f"✅ Termination job started: {job_id}")
        return True
    except Exception as e:
        print(f"❌ Error terminating recovery instances: {e}")
        return False


def stop_drs_jobs(region: str, job_ids: List[str], dry_run: bool = False) -> bool:
    """Stop active DRS jobs to resolve conflicts."""
    if not job_ids:
        return True
    
    drs_client = boto3.client('drs', region_name=region)
    
    print(f"{'[DRY RUN] ' if dry_run else ''}Stopping {len(job_ids)} DRS jobs...")
    
    success_count = 0
    for job_id in job_ids:
        print(f"  - {job_id}")
        
        if dry_run:
            success_count += 1
            continue
        
        try:
            response = drs_client.stop_replication(
                sourceServerID=job_id  # This might need adjustment based on job structure
            )
            success_count += 1
        except Exception as e:
            print(f"    ❌ Error stopping job {job_id}: {e}")
    
    if not dry_run:
        print(f"✅ Successfully stopped {success_count}/{len(job_ids)} jobs")
    
    return success_count == len(job_ids)


def analyze_conflicts(region: str) -> Dict[str, Any]:
    """Analyze DRS conflicts and provide resolution recommendations."""
    print(f"🔍 Analyzing DRS conflicts in region: {region}")
    
    # Get active jobs
    active_jobs = get_active_drs_jobs(region)
    print(f"Found {len(active_jobs)} active DRS jobs")
    
    # Get recovery instances
    recovery_instances = get_recovery_instances(region)
    print(f"Found {len(recovery_instances)} recovery instances")
    
    # Analyze conflicts
    conflicts = {
        'active_jobs': active_jobs,
        'recovery_instances': recovery_instances,
        'conflicting_servers': set(),
        'recommendations': []
    }
    
    # Extract conflicting server IDs from active jobs
    for job in active_jobs:
        job_id = job.get('jobID', 'unknown')
        status = job.get('status', 'unknown')
        job_type = job.get('type', 'unknown')
        
        print(f"\n📋 Active Job: {job_id}")
        print(f"   Status: {status}")
        print(f"   Type: {job_type}")
        
        participating_servers = job.get('participatingServers', [])
        for server in participating_servers:
            server_id = server.get('sourceServerID')
            launch_status = server.get('launchStatus', 'unknown')
            
            if server_id:
                conflicts['conflicting_servers'].add(server_id)
                print(f"   Server: {server_id} (Status: {launch_status})")
    
    # Extract recovery instance IDs
    recovery_instance_ids = []
    for instance in recovery_instances:
        instance_id = instance.get('recoveryInstanceID')
        if instance_id:
            recovery_instance_ids.append(instance_id)
            print(f"\n🖥️  Recovery Instance: {instance_id}")
            print(f"   Source Server: {instance.get('sourceServerID', 'unknown')}")
            print(f"   EC2 Instance: {instance.get('ec2InstanceID', 'unknown')}")
    
    # Generate recommendations
    if active_jobs:
        conflicts['recommendations'].append(
            f"Terminate {len(recovery_instance_ids)} recovery instances to stop active jobs"
        )
    
    if recovery_instances:
        conflicts['recommendations'].append(
            f"Clean up {len(recovery_instances)} existing recovery instances"
        )
    
    if not active_jobs and not recovery_instances:
        conflicts['recommendations'].append("No conflicts detected - DRS is ready for new executions")
    
    return conflicts


def main():
    parser = argparse.ArgumentParser(description='Resolve DRS job conflicts')
    parser.add_argument('--region', required=True, help='AWS region (e.g., us-west-2)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--auto-fix', action='store_true', help='Automatically fix conflicts')
    
    args = parser.parse_args()
    
    print("🚀 DRS Conflict Resolution Tool")
    print("=" * 50)
    
    # Analyze conflicts
    conflicts = analyze_conflicts(args.region)
    
    print(f"\n📊 Conflict Analysis Summary:")
    print(f"   Active Jobs: {len(conflicts['active_jobs'])}")
    print(f"   Recovery Instances: {len(conflicts['recovery_instances'])}")
    print(f"   Conflicting Servers: {len(conflicts['conflicting_servers'])}")
    
    print(f"\n💡 Recommendations:")
    for i, rec in enumerate(conflicts['recommendations'], 1):
        print(f"   {i}. {rec}")
    
    # Auto-fix if requested
    if args.auto_fix and (conflicts['active_jobs'] or conflicts['recovery_instances']):
        print(f"\n🔧 Auto-fixing conflicts...")
        
        # Terminate recovery instances
        recovery_instance_ids = [
            instance.get('recoveryInstanceID') 
            for instance in conflicts['recovery_instances']
            if instance.get('recoveryInstanceID')
        ]
        
        if recovery_instance_ids:
            success = terminate_recovery_instances(args.region, recovery_instance_ids, args.dry_run)
            if success:
                print("✅ Recovery instances terminated successfully")
            else:
                print("❌ Failed to terminate some recovery instances")
                sys.exit(1)
        
        print("✅ Conflict resolution completed")
    
    elif conflicts['active_jobs'] or conflicts['recovery_instances']:
        print(f"\n⚠️  Conflicts detected! Run with --auto-fix to resolve automatically")
        print(f"   Or use --dry-run to see what would be changed")
        sys.exit(1)
    
    else:
        print(f"\n✅ No conflicts detected - DRS is ready for new executions")


if __name__ == '__main__':
    main()