#!/usr/bin/env python3
"""
DRS Stuck Job Cleanup Automation
Clears stuck/orphaned DRS recovery jobs automatically

Usage:
    python3 scripts/cleanup_stuck_drs_jobs.py [--region REGION] [--dry-run]

Features:
- Automatic diagnostic phase (find jobs, instances, conversion servers)
- Intelligent scenario detection (orphaned instances, conversion servers, or stuck jobs)
- Automated cleanup execution (no manual input required)
- Comprehensive logging (see every step)
- Verification phase (confirm clean state)
"""

import argparse
import boto3
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

class DRSJobCleaner:
    """Automated cleanup for stuck DRS recovery jobs"""
    
    def __init__(self, region: str = 'us-east-1', dry_run: bool = False):
        """
        Initialize DRS Job Cleaner
        
        Args:
            region: AWS region to operate in
            dry_run: If True, only diagnose without taking action
        """
        self.region = region
        self.dry_run = dry_run
        self.drs = boto3.client('drs', region_name=region)
        self.ec2 = boto3.client('ec2', region_name=region)
        
        print(f"✓ Initialized DRS Job Cleaner")
        print(f"  Region: {region}")
        print(f"  Dry-run mode: {dry_run}")
        print()
    
    def phase_1_diagnostics(self) -> Dict:
        """
        Phase 1: Find stuck jobs and resources
        
        Returns:
            Dictionary containing diagnostic data:
            - stuck_jobs: List of jobs in PENDING/STARTED state
            - recovery_instances: List of running recovery instances
            - conversion_servers: List of running conversion servers
            - source_servers: List of affected source servers
        """
        print("=" * 70)
        print("PHASE 1: DIAGNOSTICS")
        print("=" * 70)
        
        # Get jobs from last 3 hours
        three_hours_ago = datetime.utcnow() - timedelta(hours=3)
        
        print(f"\n1. Querying DRS jobs since {three_hours_ago.strftime('%Y-%m-%d %H:%M:%S UTC')}...")
        
        try:
            jobs_response = self.drs.describe_jobs(
                filters={
                    'fromDate': three_hours_ago.strftime('%Y-%m-%dT%H:%M:%S') + 'Z'
                }
            )
            
            all_jobs = jobs_response.get('items', [])
            stuck_jobs = [j for j in all_jobs if j['status'] in ['PENDING', 'STARTED']]
            
            print(f"   Found {len(all_jobs)} total jobs, {len(stuck_jobs)} stuck (PENDING/STARTED)")
            
            for job in stuck_jobs:
                job_id = job['jobID']
                status = job['status']
                server_count = len(job.get('participatingServers', []))
                print(f"   - Job {job_id}: Status={status}, Servers={server_count}")
                
        except Exception as e:
            print(f"   ⚠️  Error querying jobs: {e}")
            stuck_jobs = []
        
        # Check for recovery instances
        print("\n2. Checking for running recovery instances...")
        
        try:
            instances_response = self.ec2.describe_instances(
                Filters=[
                    {'Name': 'tag:AWSElasticDisasterRecoveryDrillInstance', 'Values': ['*']},
                    {'Name': 'instance-state-name', 'Values': ['pending', 'running', 'stopping', 'stopped']}
                ]
            )
            
            recovery_instances = []
            for reservation in instances_response.get('Reservations', []):
                for instance in reservation.get('Instances', []):
                    recovery_instances.append({
                        'instance_id': instance['InstanceId'],
                        'state': instance['State']['Name'],
                        'launch_time': instance.get('LaunchTime', 'Unknown')
                    })
            
            print(f"   Found {len(recovery_instances)} recovery instances")
            for inst in recovery_instances:
                print(f"   - {inst['instance_id']}: State={inst['state']}, LaunchTime={inst['launch_time']}")
                
        except Exception as e:
            print(f"   ⚠️  Error querying recovery instances: {e}")
            recovery_instances = []
        
        # Check for conversion servers
        print("\n3. Checking for running conversion servers...")
        
        try:
            conversion_response = self.ec2.describe_instances(
                Filters=[
                    {'Name': 'tag:AWSElasticDisasterRecoveryConversionServer', 'Values': ['*']},
                    {'Name': 'instance-state-name', 'Values': ['pending', 'running']}
                ]
            )
            
            conversion_servers = []
            for reservation in conversion_response.get('Reservations', []):
                for instance in reservation.get('Instances', []):
                    conversion_servers.append({
                        'instance_id': instance['InstanceId'],
                        'state': instance['State']['Name'],
                        'launch_time': instance.get('LaunchTime', 'Unknown')
                    })
            
            print(f"   Found {len(conversion_servers)} conversion servers")
            for server in conversion_servers:
                print(f"   - {server['instance_id']}: State={server['state']}")
                
        except Exception as e:
            print(f"   ⚠️  Error querying conversion servers: {e}")
            conversion_servers = []
        
        # Get source server states
        print("\n4. Checking source server states...")
        
        source_servers = []
        for job in stuck_jobs:
            for server in job.get('participatingServers', []):
                server_id = server.get('sourceServerID')
                if server_id:
                    source_servers.append(server_id)
        
        if source_servers:
            try:
                servers_response = self.drs.describe_source_servers(
                    filters={'sourceServerIDs': list(set(source_servers))}
                )
                
                print(f"   Checked {len(servers_response.get('items', []))} source servers")
                for server in servers_response.get('items', []):
                    server_id = server['sourceServerID']
                    repl_state = server.get('dataReplicationInfo', {}).get('dataReplicationState', 'Unknown')
                    last_recovery = server.get('lifeCycle', {}).get('lastRecovery', {}).get('status', 'None')
                    print(f"   - {server_id}: ReplicationState={repl_state}, LastRecovery={last_recovery}")
                    
            except Exception as e:
                print(f"   ⚠️  Error querying source servers: {e}")
        else:
            print("   No source servers to check")
        
        print("\n" + "=" * 70)
        
        return {
            'stuck_jobs': stuck_jobs,
            'recovery_instances': recovery_instances,
            'conversion_servers': conversion_servers,
            'source_servers': source_servers
        }
    
    def identify_scenario(self, diagnostic_data: Dict) -> Tuple[str, str]:
        """
        Identify which cleanup scenario applies
        
        Args:
            diagnostic_data: Results from phase_1_diagnostics
            
        Returns:
            Tuple of (scenario_code, description)
            Scenarios:
            - A: Recovery instances found (terminate via DRS API)
            - B: Conversion servers found (terminate via EC2)
            - C: Jobs stuck with no resources (wait or manual intervention)
        """
        print("SCENARIO IDENTIFICATION")
        print("=" * 70)
        
        recovery_instances = diagnostic_data['recovery_instances']
        conversion_servers = diagnostic_data['conversion_servers']
        stuck_jobs = diagnostic_data['stuck_jobs']
        
        if recovery_instances:
            scenario = 'A'
            desc = f"Recovery instances found ({len(recovery_instances)} instances)"
            print(f"\n✓ Scenario A: {desc}")
            print("  Action: Terminate recovery instances via DRS API")
            print("  Why: Instances launched but monitoring lost track")
            print("  Result: DRS API cleans up metadata, clears job state")
            
        elif conversion_servers:
            scenario = 'B'
            desc = f"Conversion servers found ({len(conversion_servers)} servers)"
            print(f"\n✓ Scenario B: {desc}")
            print("  Action: Terminate conversion servers via EC2")
            print("  Why: Conversion process stuck/deadlocked")
            print("  Result: Forces job to fail, clears stuck state")
            
        elif stuck_jobs:
            scenario = 'C'
            desc = f"Jobs stuck with no resources ({len(stuck_jobs)} jobs)"
            print(f"\n✓ Scenario C: {desc}")
            print("  Action: Wait for DRS internal timeout (4 hours max)")
            print("  Why: Jobs stuck in DRS service state")
            print("  Result: Will auto-fail after timeout, or need AWS Support")
            
        else:
            scenario = 'NONE'
            desc = "No stuck jobs or resources found"
            print(f"\n✓ Scenario: {desc}")
            print("  Action: None needed")
            print("  Result: System is clean")
        
        print("=" * 70 + "\n")
        
        return scenario, desc
    
    def phase_2_cleanup(self, scenario: str, diagnostic_data: Dict) -> bool:
        """
        Phase 2: Execute cleanup based on scenario
        
        Args:
            scenario: Scenario code from identify_scenario
            diagnostic_data: Results from phase_1_diagnostics
            
        Returns:
            True if cleanup successful, False otherwise
        """
        print("=" * 70)
        print("PHASE 2: CLEANUP")
        print("=" * 70)
        
        if self.dry_run:
            print("\n⚠️  DRY-RUN MODE: No actual cleanup will be performed\n")
        
        if scenario == 'A':
            return self._cleanup_scenario_a(diagnostic_data)
        elif scenario == 'B':
            return self._cleanup_scenario_b(diagnostic_data)
        elif scenario == 'C':
            return self._cleanup_scenario_c(diagnostic_data)
        else:
            print("\n✓ No cleanup needed - system is clean")
            return True
    
    def _cleanup_scenario_a(self, data: Dict) -> bool:
        """Scenario A: Terminate recovery instances via DRS API"""
        
        print("\nExecuting Scenario A: Recovery Instance Termination")
        print("-" * 70)
        
        recovery_instances = data['recovery_instances']
        instance_ids = [inst['instance_id'] for inst in recovery_instances]
        
        print(f"\nTerminating {len(instance_ids)} recovery instances:")
        for inst_id in instance_ids:
            print(f"  - {inst_id}")
        
        if self.dry_run:
            print("\n[DRY-RUN] Would execute:")
            print(f"  drs.terminate_recovery_instances(recoveryInstanceIDs={instance_ids})")
            return True
        
        try:
            print("\nExecuting termination...")
            response = self.drs.terminate_recovery_instances(
                recoveryInstanceIDs=instance_ids
            )
            
            print("✓ Termination initiated successfully")
            print(f"  Response: {response.get('ResponseMetadata', {}).get('HTTPStatusCode', 'Unknown')}")
            
            # Wait a moment for termination to start
            print("\nWaiting 10 seconds for termination to process...")
            time.sleep(10)
            
            return True
            
        except Exception as e:
            print(f"✗ Error terminating instances: {e}")
            return False
    
    def _cleanup_scenario_b(self, data: Dict) -> bool:
        """Scenario B: Terminate conversion servers via EC2"""
        
        print("\nExecuting Scenario B: Conversion Server Termination")
        print("-" * 70)
        
        conversion_servers = data['conversion_servers']
        instance_ids = [server['instance_id'] for server in conversion_servers]
        
        print(f"\nTerminating {len(instance_ids)} conversion servers:")
        for inst_id in instance_ids:
            print(f"  - {inst_id}")
        
        if self.dry_run:
            print("\n[DRY-RUN] Would execute:")
            print(f"  ec2.terminate_instances(InstanceIds={instance_ids})")
            return True
        
        try:
            print("\nExecuting termination...")
            response = self.ec2.terminate_instances(
                InstanceIds=instance_ids
            )
            
            print("✓ Termination initiated successfully")
            terminated = response.get('TerminatingInstances', [])
            for inst in terminated:
                print(f"  - {inst['InstanceId']}: {inst['PreviousState']['Name']} → {inst['CurrentState']['Name']}")
            
            # Wait a moment for termination to start
            print("\nWaiting 10 seconds for termination to process...")
            time.sleep(10)
            
            return True
            
        except Exception as e:
            print(f"✗ Error terminating conversion servers: {e}")
            return False
    
    def _cleanup_scenario_c(self, data: Dict) -> bool:
        """Scenario C: Jobs stuck with no resources"""
        
        print("\nScenario C: Jobs Stuck in DRS Service State")
        print("-" * 70)
        
        stuck_jobs = data['stuck_jobs']
        
        print(f"\nFound {len(stuck_jobs)} stuck jobs with no associated resources:")
        for job in stuck_jobs:
            print(f"  - Job {job['jobID']}: Status={job['status']}")
        
        print("\n⚠️  These jobs cannot be cleaned up automatically.")
        print("\nOptions:")
        print("  1. Wait for DRS internal timeout (4-hour maximum)")
        print("  2. Check AWS DRS Console for manual 'Cancel' option")
        print("  3. Open AWS Support case if urgent")
        
        print("\nRecommendation: Wait 2 more hours for auto-timeout")
        print("Current time:", datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'))
        print("Expected timeout:", (datetime.utcnow() + timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S UTC'))
        
        return False  # Cannot auto-clean scenario C
    
    def phase_3_verify(self) -> bool:
        """
        Phase 3: Verify clean state achieved
        
        Returns:
            True if system is clean, False otherwise
        """
        print("\n" + "=" * 70)
        print("PHASE 3: VERIFICATION")
        print("=" * 70)
        
        # Check for stuck jobs
        print("\n1. Verifying no stuck jobs remain...")
        
        try:
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            jobs_response = self.drs.describe_jobs(
                filters={
                    'fromDate': one_hour_ago.strftime('%Y-%m-%dT%H:%M:%S') + 'Z'
                }
            )
            
            stuck_jobs = [j for j in jobs_response.get('items', []) 
                         if j['status'] in ['PENDING', 'STARTED']]
            
            if stuck_jobs:
                print(f"   ✗ Still found {len(stuck_jobs)} stuck jobs")
                for job in stuck_jobs:
                    print(f"      - Job {job['jobID']}: Status={job['status']}")
                jobs_clean = False
            else:
                print("   ✓ No stuck jobs found")
                jobs_clean = True
                
        except Exception as e:
            print(f"   ⚠️  Error checking jobs: {e}")
            jobs_clean = False
        
        # Check for recovery instances
        print("\n2. Verifying no recovery instances remain...")
        
        try:
            instances_response = self.ec2.describe_instances(
                Filters=[
                    {'Name': 'tag:AWSElasticDisasterRecoveryDrillInstance', 'Values': ['*']},
                    {'Name': 'instance-state-name', 'Values': ['running']}
                ]
            )
            
            running_instances = []
            for reservation in instances_response.get('Reservations', []):
                for instance in reservation.get('Instances', []):
                    running_instances.append(instance['InstanceId'])
            
            if running_instances:
                print(f"   ✗ Still found {len(running_instances)} running recovery instances")
                for inst_id in running_instances:
                    print(f"      - {inst_id}")
                instances_clean = False
            else:
                print("   ✓ No recovery instances running")
                instances_clean = True
                
        except Exception as e:
            print(f"   ⚠️  Error checking instances: {e}")
            instances_clean = False
        
        # Check for conversion servers
        print("\n3. Verifying no conversion servers remain...")
        
        try:
            conversion_response = self.ec2.describe_instances(
                Filters=[
                    {'Name': 'tag:AWSElasticDisasterRecoveryConversionServer', 'Values': ['*']},
                    {'Name': 'instance-state-name', 'Values': ['running']}
                ]
            )
            
            running_servers = []
            for reservation in conversion_response.get('Reservations', []):
                for instance in reservation.get('Instances', []):
                    running_servers.append(instance['InstanceId'])
            
            if running_servers:
                print(f"   ✗ Still found {len(running_servers)} running conversion servers")
                for server_id in running_servers:
                    print(f"      - {server_id}")
                servers_clean = False
            else:
                print("   ✓ No conversion servers running")
                servers_clean = True
                
        except Exception as e:
            print(f"   ⚠️  Error checking conversion servers: {e}")
            servers_clean = False
        
        # Overall verification
        print("\n" + "=" * 70)
        all_clean = jobs_clean and instances_clean and servers_clean
        
        if all_clean:
            print("✓ VERIFICATION PASSED: System is clean")
            print("\nSource servers should now be:")
            print("  - Ready for recovery: Yes")
            print("  - Data replication status: Healthy")
            print("  - Last recovery result: COMPLETED or FAILED (not PENDING)")
        else:
            print("✗ VERIFICATION FAILED: System not fully clean")
            print("\nSome resources may still be terminating.")
            print("Wait 5-10 minutes and re-run this script to verify.")
        
        print("=" * 70)
        
        return all_clean
    
    def run(self) -> int:
        """
        Main execution flow
        
        Returns:
            Exit code: 0 for success, 1 for failure
        """
        print("\n" + "=" * 70)
        print(" " * 15 + "DRS STUCK JOB CLEANUP AUTOMATION")
        print("=" * 70)
        print(f"Start time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print("=" * 70 + "\n")
        
        try:
            # Phase 1: Diagnostics
            diagnostic_data = self.phase_1_diagnostics()
            
            # Identify scenario
            scenario, description = self.identify_scenario(diagnostic_data)
            
            # Phase 2: Cleanup
            cleanup_success = self.phase_2_cleanup(scenario, diagnostic_data)
            
            if not cleanup_success:
                print("\n⚠️  Cleanup could not be completed automatically")
                if scenario == 'C':
                    print("   Jobs will timeout eventually (up to 4 hours)")
                    print("   Or open AWS Support case for manual intervention")
                return 1
            
            # Phase 3: Verification
            if not self.dry_run:
                verified = self.phase_3_verify()
                
                if verified:
                    print("\n✓ SUCCESS: Cleanup completed and verified")
                    print("\nNext steps:")
                    print("  1. Verify in DRS Console that servers show 'Ready for recovery'")
                    print("  2. Check 'Last recovery result' no longer shows 'Pending'")
                    print("  3. Retry drill manually via console to test")
                    return 0
                else:
                    print("\n⚠️  Cleanup initiated but verification incomplete")
                    print("   Resources may still be terminating")
                    print("   Wait 5-10 minutes and verify manually")
                    return 1
            else:
                print("\n✓ DRY-RUN COMPLETED: No actual changes made")
                print("\nRun without --dry-run to execute cleanup")
                return 0
                
        except Exception as e:
            print(f"\n✗ FATAL ERROR: {e}")
            import traceback
            traceback.print_exc()
            return 1
        
        finally:
            print("\n" + "=" * 70)
            print(f"End time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
            print("=" * 70 + "\n")


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Automated cleanup for stuck DRS recovery jobs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run cleanup in us-east-1
  python3 scripts/cleanup_stuck_drs_jobs.py
  
  # Run in different region
  python3 scripts/cleanup_stuck_drs_jobs.py --region us-west-2
  
  # Dry-run mode (diagnostics only)
  python3 scripts/cleanup_stuck_drs_jobs.py --dry-run
        """
    )
    
    parser.add_argument(
        '--region',
        default='us-east-1',
        help='AWS region to operate in (default: us-east-1)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run diagnostics only, do not perform cleanup'
    )
    
    args = parser.parse_args()
    
    # Create and run cleaner
    cleaner = DRSJobCleaner(region=args.region, dry_run=args.dry_run)
    exit_code = cleaner.run()
    
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
