#!/usr/bin/env python3
"""
DRS Drill Monitor - Complete lifecycle monitoring script
Monitors a DRS drill job from initiation to completion
"""

import boto3
import json
import time
from datetime import datetime

def monitor_drill(job_id, timeout=1200):
    """Monitor DRS drill job with 30s polling"""
    drs = boto3.client('drs', region_name='us-east-1')
    
    print('=' * 80)
    print('DRS DRILL MONITORING')
    print('=' * 80)
    print(f'Job ID: {job_id}')
    print(f'Polling every 30s (timeout: {timeout}s / {timeout//60}min)')
    print()
    
    start_time = time.time()
    poll_count = 0
    previous_status = None
    status_changes = []
    
    results = {
        'job_id': job_id,
        'start_time': datetime.now().isoformat(),
        'polls': [],
        'status_changes': [],
        'final_status': None,
        'recovery_instance_id': None,
        'elapsed_time': 0
    }
    
    try:
        while time.time() - start_time < timeout:
            poll_count += 1
            elapsed = int(time.time() - start_time)
            
            # Query job status
            response = drs.describe_jobs(filters={'jobIDs': [job_id]})
            
            if not response.get('items'):
                print(f'❌ Job not found: {job_id}')
                results['error'] = 'Job not found'
                break
            
            job = response['items'][0]
            job_status = job.get('status')
            
            # Print status
            timestamp = datetime.now().strftime('%H:%M:%S')
            print(f'[{timestamp}] Poll #{poll_count} (T+{elapsed}s): {job_status}')
            
            # Show servers
            servers = job.get('participatingServers', [])
            for server in servers:
                srv_id = server.get('sourceServerID')
                launch_status = server.get('launchStatus', 'N/A')
                rec_id = server.get('recoveryInstanceID')
                print(f'  {srv_id}: {launch_status}', end='')
                if rec_id:
                    print(f' → {rec_id}')
                    results['recovery_instance_id'] = rec_id
                else:
                    print()
            
            # Track status change
            if job_status != previous_status:
                change = f'{previous_status or "INIT"} → {job_status}'
                print(f'  📊 STATUS CHANGE: {change}')
                status_changes.append({
                    'timestamp': datetime.now().isoformat(),
                    'elapsed': elapsed,
                    'change': change
                })
            previous_status = job_status
            print()
            
            # Save poll data
            results['polls'].append({
                'poll_num': poll_count,
                'elapsed': elapsed,
                'status': job_status,
                'servers': [{
                    'sourceServerID': s.get('sourceServerID'),
                    'launchStatus': s.get('launchStatus'),
                    'recoveryInstanceID': s.get('recoveryInstanceID')
                } for s in servers]
            })
            
            # Check completion
            if job_status == 'COMPLETED':
                print('=' * 80)
                print('✅ JOB COMPLETED SUCCESSFULLY!')
                print('=' * 80)
                results['final_status'] = 'COMPLETED'
                results['elapsed_time'] = elapsed
                results['status_changes'] = status_changes
                
                # Save full job details
                results['final_job'] = json.loads(json.dumps(job, default=str))
                break
                
            elif job_status == 'FAILED':
                print('=' * 80)
                print('❌ JOB FAILED!')
                print('=' * 80)
                results['final_status'] = 'FAILED'
                results['elapsed_time'] = elapsed
                results['status_changes'] = status_changes
                results['final_job'] = json.loads(json.dumps(job, default=str))
                break
            
            # Wait 30s before next poll
            time.sleep(30)
        else:
            # Timeout reached
            print(f'⏱️ Timeout after {timeout}s')
            results['final_status'] = f'TIMEOUT at {job_status}'
            results['elapsed_time'] = timeout
            
    except Exception as e:
        print(f'❌ Error: {e}')
        results['error'] = str(e)
        import traceback
        traceback.print_exc()
    
    # Write results
    results_file = f'/tmp/drs_drill_results_{job_id}.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    print()
    print(f'Results saved: {results_file}')
    
    # Also write recovery instance ID if available
    if results.get('recovery_instance_id'):
        with open('/tmp/drs_recovery_instance_id.txt', 'w') as f:
            f.write(results['recovery_instance_id'])
    
    return results

if __name__ == '__main__':
    # Read job ID from temp file
    with open('/tmp/drs_drill_job_id.txt', 'r') as f:
        job_id = f.read().strip()
    
    results = monitor_drill(job_id)
    
    # Print summary
    print()
    print('=' * 80)
    print('MONITORING COMPLETE')
    print('=' * 80)
    print(f'Final Status: {results.get("final_status")}')
    print(f'Total Time: {results.get("elapsed_time")}s')
    print(f'Polls: {len(results.get("polls", []))}')
    print(f'Status Changes: {len(results.get("status_changes", []))}')
    if results.get('recovery_instance_id'):
        print(f'Recovery Instance: {results.get("recovery_instance_id")}')
