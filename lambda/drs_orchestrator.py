"""
Step Functions Orchestration Lambda
Based on proven drs-plan-automation reference implementation

CRITICAL FIX: Removed 'tags' parameter from start_recovery() call
The reference implementation does NOT use tags, and CLI without tags works.
"""

import boto3
import json
import os
import time
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Any

# Environment variables
PROTECTION_GROUPS_TABLE = os.environ.get('PROTECTION_GROUPS_TABLE')
RECOVERY_PLANS_TABLE = os.environ.get('RECOVERY_PLANS_TABLE')
EXECUTION_HISTORY_TABLE = os.environ.get('EXECUTION_HISTORY_TABLE')

# AWS clients
dynamodb = boto3.resource('dynamodb')

# DynamoDB tables (lazy init)
_protection_groups_table = None
_recovery_plans_table = None
_execution_history_table = None


def get_protection_groups_table():
    global _protection_groups_table
    if _protection_groups_table is None:
        _protection_groups_table = dynamodb.Table(PROTECTION_GROUPS_TABLE)
    return _protection_groups_table


def get_recovery_plans_table():
    global _recovery_plans_table
    if _recovery_plans_table is None:
        _recovery_plans_table = dynamodb.Table(RECOVERY_PLANS_TABLE)
    return _recovery_plans_table


def get_execution_history_table():
    global _execution_history_table
    if _execution_history_table is None:
        _execution_history_table = dynamodb.Table(EXECUTION_HISTORY_TABLE)
    return _execution_history_table


# DRS job status constants (from reference implementation)
DRS_JOB_STATUS_COMPLETE_STATES = ['COMPLETED']
DRS_JOB_STATUS_WAIT_STATES = ['PENDING', 'STARTED']

# DRS server launch status constants (CRITICAL - this is what we were missing!)
DRS_JOB_SERVERS_COMPLETE_SUCCESS_STATES = ['LAUNCHED']
DRS_JOB_SERVERS_COMPLETE_FAILURE_STATES = ['FAILED', 'TERMINATED']
DRS_JOB_SERVERS_WAIT_STATES = ['PENDING', 'IN_PROGRESS']


class DecimalEncoder(json.JSONEncoder):
    """Handle Decimal types from DynamoDB"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super(DecimalEncoder, self).default(obj)


def lambda_handler(event, context):
    """
    Step Functions orchestration handler
    
    Actions (api-stack.yaml state machine):
    - initialize: Initialize execution and return waves
    - processWave: Process a single wave (start DRS recovery)
    - finalize: Finalize execution
    
    Actions (step-functions-stack.yaml state machine):
    - begin: Initialize wave plan execution
    - update_wave_status: Poll DRS job and check server launch status
    """
    print(f"Event: {json.dumps(event, cls=DecimalEncoder)}")
    
    action = event.get('action')
    
    # api-stack.yaml state machine actions
    if action == 'initialize':
        return initialize_execution(event)
    elif action == 'processWave':
        return process_wave(event)
    elif action == 'finalize':
        return finalize_execution(event)
    # step-functions-stack.yaml state machine actions
    elif action == 'begin':
        return begin_wave_plan(event)
    elif action == 'update_wave_status':
        return update_wave_status(event)
    else:
        raise ValueError(f"Unknown action: {action}")


def initialize_execution(event: Dict) -> Dict:
    """
    Initialize execution for api-stack.yaml state machine
    Returns waves array for Map state processing
    """
    execution_id = event.get('executionId')
    input_data = event.get('input', {})
    
    # Extract plan info from input
    plans = input_data.get('Plans', [])
    is_drill = input_data.get('IsDrill', True)
    
    if not plans:
        print("No plans provided")
        return {'waves': [], 'executionId': execution_id, 'status': 'failed', 'error': 'No plans provided'}
    
    plan = plans[0]  # Use first plan
    plan_id = plan.get('PlanId')
    waves = plan.get('Waves', [])
    
    print(f"Initializing execution {execution_id} for plan {plan_id}")
    print(f"Total waves: {len(waves)}, isDrill: {is_drill}")
    
    # Update DynamoDB execution status
    try:
        get_execution_history_table().update_item(
            Key={'ExecutionId': execution_id, 'PlanId': plan_id},
            UpdateExpression='SET #status = :status',
            ExpressionAttributeNames={'#status': 'Status'},
            ExpressionAttributeValues={':status': 'RUNNING'}
        )
    except Exception as e:
        print(f"Error updating execution status: {e}")
    
    # Prepare waves with execution context
    waves_with_context = []
    for i, wave in enumerate(waves):
        waves_with_context.append({
            **wave,
            'executionId': execution_id,
            'planId': plan_id,
            'isDrill': is_drill,
            'waveIndex': i
        })
    
    return {
        'waves': waves_with_context,
        'executionId': execution_id,
        'planId': plan_id,
        'isDrill': is_drill,
        'status': 'initialized'
    }


def process_wave(event: Dict) -> Dict:
    """
    Process a single wave - start DRS recovery
    Called by Map state in api-stack.yaml state machine
    """
    wave = event.get('wave', event)  # wave data passed directly or nested
    execution_id = wave.get('executionId') or event.get('executionId')
    plan_id = wave.get('planId')
    is_drill = wave.get('isDrill', True)
    wave_index = wave.get('waveIndex', 0)
    wave_name = wave.get('WaveName', f'Wave {wave_index + 1}')
    
    print(f"Processing wave {wave_index} ({wave_name}) for execution {execution_id}")
    
    # Get Protection Group to find servers and region
    protection_group_id = wave.get('ProtectionGroupId')
    if not protection_group_id:
        print(f"Wave {wave_index} has no ProtectionGroupId")
        return {'status': 'failed', 'error': 'No ProtectionGroupId', 'waveIndex': wave_index}
    
    try:
        # Get Protection Group
        pg_response = get_protection_groups_table().get_item(Key={'GroupId': protection_group_id})
        if 'Item' not in pg_response:
            return {'status': 'failed', 'error': f'Protection Group {protection_group_id} not found', 'waveIndex': wave_index}
        
        pg = pg_response['Item']
        server_ids = wave.get('ServerIds', pg.get('SourceServerIds', []))
        region = pg.get('Region', 'us-east-1')
        
        if not server_ids:
            print(f"Wave {wave_index} has no servers, marking complete")
            return {'status': 'completed', 'waveIndex': wave_index, 'message': 'No servers in wave'}
        
        print(f"Starting DRS recovery for wave {wave_index}")
        print(f"Region: {region}, Servers: {server_ids}, isDrill: {is_drill}")
        
        # Create DRS client for the region
        drs_client = boto3.client('drs', region_name=region)
        
        # Build sourceServers array
        source_servers = [{'sourceServerID': sid} for sid in server_ids]
        
        # Start DRS recovery WITHOUT tags (critical fix)
        response = drs_client.start_recovery(
            isDrill=is_drill,
            sourceServers=source_servers
        )
        
        job_id = response['job']['jobID']
        job_status = response['job'].get('status', 'UNKNOWN')
        
        print(f"DRS Job created: {job_id}, Status: {job_status}")
        
        # Update DynamoDB with wave start
        try:
            wave_result = {
                'WaveNumber': wave_index,
                'WaveName': wave_name,
                'Status': 'STARTED',
                'JobId': job_id,
                'StartTime': int(time.time()),
                'ServerIds': server_ids,
                'Region': region
            }
            get_execution_history_table().update_item(
                Key={'ExecutionId': execution_id, 'PlanId': plan_id},
                UpdateExpression='SET Waves = list_append(if_not_exists(Waves, :empty), :wave)',
                ExpressionAttributeValues={
                    ':empty': [],
                    ':wave': [wave_result]
                }
            )
        except Exception as e:
            print(f"Error updating wave in DynamoDB: {e}")
        
        return {
            'status': 'started',
            'waveIndex': wave_index,
            'waveName': wave_name,
            'jobId': job_id,
            'region': region,
            'serverIds': server_ids
        }
        
    except Exception as e:
        print(f"Error processing wave: {e}")
        import traceback
        traceback.print_exc()
        return {'status': 'failed', 'error': str(e), 'waveIndex': wave_index}


def finalize_execution(event: Dict) -> Dict:
    """
    Finalize execution after all waves processed
    """
    execution_id = event.get('executionId')
    results = event.get('results', [])
    
    print(f"Finalizing execution {execution_id}")
    print(f"Wave results: {results}")
    
    # Check if any waves failed
    failed_waves = [r for r in results if r.get('status') == 'failed']
    
    if failed_waves:
        status = 'PARTIAL' if len(failed_waves) < len(results) else 'FAILED'
    else:
        status = 'COMPLETED'
    
    # Note: We can't easily get plan_id here, so we'll update by execution_id pattern
    # The actual status update should happen in the API handler or via polling
    
    return {
        'executionId': execution_id,
        'status': status,
        'totalWaves': len(results),
        'failedWaves': len(failed_waves),
        'results': results
    }


def begin_wave_plan(event: Dict) -> Dict:
    """
    Initialize wave plan execution
    
    Returns application state with first wave started
    """
    plan = event.get('plan', {})
    execution_id = event.get('execution')
    is_drill = event.get('isDrill', True)
    
    plan_id = plan.get('PlanId')
    waves = plan.get('Waves', [])
    
    print(f"Beginning wave plan for execution {execution_id}, plan {plan_id}")
    print(f"Total waves: {len(waves)}, isDrill: {is_drill}")
    
    # Initialize application state (matches reference implementation structure)
    # CRITICAL: All fields must be present for Step Functions ResultSelector
    application = {
        'plan_id': plan_id,
        'execution_id': execution_id,
        'is_drill': is_drill,
        'waves': waves,
        'current_wave_number': 0,
        'all_waves_completed': False,
        'wave_completed': False,
        'current_wave_update_time': 30,  # Poll every 30 seconds
        'current_wave_total_wait_time': 0,
        'current_wave_max_wait_time': 1800,  # 30 minutes max per wave
        'status': 'running',
        'wave_results': [],
        'job_id': None,  # Will be set when wave starts
        'region': None,  # Will be set when wave starts
        'server_ids': [],  # Will be set when wave starts
        'error': None  # Must always be present for Step Functions
    }
    
    # Update DynamoDB execution status
    try:
        get_execution_history_table().update_item(
            Key={'ExecutionId': execution_id, 'PlanId': plan_id},
            UpdateExpression='SET #status = :status, StateMachineExecution = :sfn',
            ExpressionAttributeNames={'#status': 'Status'},
            ExpressionAttributeValues={
                ':status': 'RUNNING',
                ':sfn': 'Step Functions'
            }
        )
    except Exception as e:
        print(f"Error updating execution status: {e}")
    
    # Start first wave
    if len(waves) > 0:
        start_wave_recovery(application, 0)
    else:
        print("No waves to execute")
        application['all_waves_completed'] = True
        application['status'] = 'completed'
    
    return application


def start_wave_recovery(application: Dict, wave_number: int) -> None:
    """
    Start DRS recovery for a wave
    
    CRITICAL FIX: Does NOT pass 'tags' parameter to start_recovery()
    Reference implementation does not use tags, and CLI without tags works.
    """
    waves = application['waves']
    wave = waves[wave_number]
    is_drill = application['is_drill']
    execution_id = application['execution_id']
    
    wave_name = wave.get('WaveName', f'Wave {wave_number + 1}')
    
    # Get Protection Group to find servers and region
    protection_group_id = wave.get('ProtectionGroupId')
    if not protection_group_id:
        print(f"Wave {wave_number} has no ProtectionGroupId")
        application['wave_completed'] = True
        application['status'] = 'failed'
        application['error'] = 'No ProtectionGroupId in wave'
        return
    
    try:
        # Get Protection Group
        pg_response = get_protection_groups_table().get_item(Key={'GroupId': protection_group_id})
        if 'Item' not in pg_response:
            print(f"Protection Group {protection_group_id} not found")
            application['wave_completed'] = True
            application['status'] = 'failed'
            application['error'] = f'Protection Group {protection_group_id} not found'
            return
        
        pg = pg_response['Item']
        server_ids = wave.get('ServerIds', pg.get('SourceServerIds', []))
        region = pg.get('Region', 'us-east-1')
        
        if not server_ids:
            print(f"Wave {wave_number} has no servers, marking complete")
            application['wave_completed'] = True
            return
        
        print(f"Starting DRS recovery for wave {wave_number} ({wave_name})")
        print(f"Region: {region}, Servers: {server_ids}, isDrill: {is_drill}")
        
        # Create DRS client for the region
        drs_client = boto3.client('drs', region_name=region)
        
        # Build sourceServers array (matches reference implementation)
        source_servers = [{'sourceServerID': sid} for sid in server_ids]
        
        # CRITICAL FIX: Start DRS recovery WITHOUT tags
        # Reference implementation: drs_client.start_recovery(isDrill=isdrill, sourceServers=servers)
        # NO TAGS! Tags were causing the conversion to be skipped.
        print(f"[DRS API] Calling start_recovery() WITHOUT tags (reference implementation pattern)")
        print(f"[DRS API]   sourceServers: {source_servers}")
        print(f"[DRS API]   isDrill: {is_drill}")
        
        response = drs_client.start_recovery(
            isDrill=is_drill,
            sourceServers=source_servers
            # NO TAGS - this is the fix!
        )
        
        job_id = response['job']['jobID']
        job_status = response['job'].get('status', 'UNKNOWN')
        
        print(f"[DRS API] ✅ Job created successfully")
        print(f"[DRS API]   Job ID: {job_id}")
        print(f"[DRS API]   Status: {job_status}")
        
        # Update application state
        application['current_wave_number'] = wave_number
        application['job_id'] = job_id
        application['region'] = region
        application['server_ids'] = server_ids
        application['wave_completed'] = False
        application['wave_start_time'] = datetime.now(timezone.utc).isoformat()
        application['current_wave_total_wait_time'] = 0
        
        # Store wave result
        wave_result = {
            'WaveNumber': wave_number,
            'WaveName': wave_name,
            'Status': 'STARTED',
            'JobId': job_id,
            'StartTime': int(time.time()),
            'ServerIds': server_ids,
            'Region': region
        }
        application['wave_results'].append(wave_result)
        
        # Update DynamoDB with wave start
        try:
            get_execution_history_table().update_item(
                Key={'ExecutionId': execution_id, 'PlanId': application['plan_id']},
                UpdateExpression='SET Waves = list_append(if_not_exists(Waves, :empty), :wave)',
                ExpressionAttributeValues={
                    ':empty': [],
                    ':wave': [wave_result]
                }
            )
        except Exception as e:
            print(f"Error updating wave start in DynamoDB: {e}")
        
    except Exception as e:
        print(f"Error starting DRS recovery: {e}")
        import traceback
        traceback.print_exc()
        application['wave_completed'] = True
        application['status'] = 'failed'
        application['error'] = str(e)


def update_wave_status(event: Dict) -> Dict:
    """
    Poll DRS job status and check server launch status
    
    CRITICAL: Checks participatingServers[].launchStatus, not just job status!
    This is the key to knowing when EC2 instances actually launch.
    """
    application = event.get('application', event)
    job_id = application.get('job_id')
    wave_number = application.get('current_wave_number', 0)
    region = application.get('region', 'us-east-1')
    execution_id = application.get('execution_id')
    plan_id = application.get('plan_id')
    
    if not job_id:
        print("No job_id found, marking wave complete")
        application['wave_completed'] = True
        return application
    
    # Update total wait time
    update_time = application.get('current_wave_update_time', 30)
    total_wait = application.get('current_wave_total_wait_time', 0) + update_time
    max_wait = application.get('current_wave_max_wait_time', 1800)
    application['current_wave_total_wait_time'] = total_wait
    
    print(f"Checking status for job {job_id} in region {region}")
    print(f"Total wait time: {total_wait}s / {max_wait}s max")
    
    # Check for timeout
    if total_wait >= max_wait:
        print(f"❌ Wave {wave_number} TIMEOUT after {total_wait}s")
        application['wave_completed'] = True
        application['status'] = 'timeout'
        application['error'] = f'Wave timed out after {total_wait}s'
        return application
    
    try:
        # Create DRS client for the region
        drs_client = boto3.client('drs', region_name=region)
        
        # Get DRS job status
        job_response = drs_client.describe_jobs(
            filters={'jobIDs': [job_id]}
        )
        
        if not job_response.get('items'):
            print(f"Job {job_id} not found")
            application['wave_completed'] = True
            application['status'] = 'failed'
            application['error'] = f'Job {job_id} not found'
            return application
        
        job = job_response['items'][0]
        job_status = job.get('status')
        
        print(f"Job {job_id} status: {job_status}")
        
        # Get job log items for detailed progress
        try:
            log_response = drs_client.describe_job_log_items(jobID=job_id)
            log_items = log_response.get('items', [])
            print(f"Job has {len(log_items)} log items")
            
            # Show recent log events
            for item in log_items[-5:]:
                event_type = item.get('event', 'UNKNOWN')
                event_data = item.get('eventData', {})
                print(f"  Log: {event_type} - {event_data}")
        except Exception as e:
            print(f"Error getting job log items: {e}")
        
        # CRITICAL: Check participating servers launch status
        participating_servers = job.get('participatingServers', [])
        
        if not participating_servers:
            print("No participating servers in job yet")
            # Job might still be initializing
            if job_status in DRS_JOB_STATUS_WAIT_STATES:
                print("Job still in wait state, continuing to poll")
                application['wave_completed'] = False
                return application
            else:
                print(f"Job status is {job_status} but no servers - marking complete")
                application['wave_completed'] = True
                return application
        
        all_launched = True
        launched_count = 0
        failed_count = 0
        pending_count = 0
        server_statuses = []
        
        for server in participating_servers:
            server_id = server.get('sourceServerID')
            launch_status = server.get('launchStatus', 'PENDING')
            recovery_instance_id = server.get('recoveryInstanceID')
            
            print(f"Server {server_id}: launchStatus={launch_status}, "
                  f"recoveryInstanceID={recovery_instance_id}")
            
            server_statuses.append({
                'SourceServerId': server_id,
                'LaunchStatus': launch_status,
                'RecoveryInstanceID': recovery_instance_id
            })
            
            if launch_status in DRS_JOB_SERVERS_COMPLETE_SUCCESS_STATES:
                # FIX: Trust LAUNCHED status - DRS doesn't always populate recoveryInstanceID
                # in the job response, but it IS populated on the source server
                launched_count += 1
                print(f"✅ Server {server_id} LAUNCHED successfully")
            elif launch_status in DRS_JOB_SERVERS_COMPLETE_FAILURE_STATES:
                failed_count += 1
                all_launched = False
                print(f"❌ Server {server_id} FAILED with status: {launch_status}")
            elif launch_status in DRS_JOB_SERVERS_WAIT_STATES:
                pending_count += 1
                all_launched = False
            else:
                print(f"Server {server_id} has unknown status: {launch_status}")
                all_launched = False
        
        total_servers = len(participating_servers)
        print(f"Wave {wave_number} progress: Launched={launched_count}, "
              f"Pending={pending_count}, Failed={failed_count}, Total={total_servers}")
        
        # CRITICAL FIX: Check if job COMPLETED but no instances were created
        # This happens when DRS skips the LAUNCH phase (our code issue)
        if job_status == 'COMPLETED' and launched_count == 0:
            print(f"❌ Wave {wave_number} FAILED - Job COMPLETED but NO recovery instances created!")
            print(f"   This indicates DRS skipped the LAUNCH phase")
            application['wave_completed'] = True
            application['status'] = 'failed'
            application['error'] = 'DRS job completed but no recovery instances were created. LAUNCH phase was skipped.'
            
            # Update DynamoDB with failure
            update_wave_in_dynamodb(execution_id, plan_id, wave_number, 'FAILED', server_statuses)
            
            try:
                get_execution_history_table().update_item(
                    Key={'ExecutionId': execution_id, 'PlanId': plan_id},
                    UpdateExpression='SET #status = :status, ErrorMessage = :error',
                    ExpressionAttributeNames={'#status': 'Status'},
                    ExpressionAttributeValues={
                        ':status': 'FAILED',
                        ':error': 'DRS job completed but no recovery instances were created'
                    }
                )
            except Exception as e:
                print(f"Error updating execution failure: {e}")
            
            return application
        
        # Check if wave is complete
        if all_launched and launched_count == total_servers:
            print(f"✅ Wave {wave_number} COMPLETE - all {launched_count} servers LAUNCHED")
            
            application['wave_completed'] = True
            application['wave_end_time'] = datetime.now(timezone.utc).isoformat()
            
            # Update wave result
            for wr in application.get('wave_results', []):
                if wr.get('WaveNumber') == wave_number:
                    wr['Status'] = 'COMPLETED'
                    wr['EndTime'] = int(time.time())
                    wr['ServerStatuses'] = server_statuses
                    break
            
            # Update DynamoDB with wave completion
            update_wave_in_dynamodb(execution_id, plan_id, wave_number, 'COMPLETED', server_statuses)
            
            # Move to next wave
            next_wave = wave_number + 1
            if next_wave < len(application.get('waves', [])):
                print(f"Starting next wave: {next_wave}")
                start_wave_recovery(application, next_wave)
            else:
                print("✅ ALL WAVES COMPLETE")
                application['all_waves_completed'] = True
                application['status'] = 'completed'
                
                # Update execution as completed
                try:
                    get_execution_history_table().update_item(
                        Key={'ExecutionId': execution_id, 'PlanId': plan_id},
                        UpdateExpression='SET #status = :status, EndTime = :end',
                        ExpressionAttributeNames={'#status': 'Status'},
                        ExpressionAttributeValues={
                            ':status': 'COMPLETED',
                            ':end': int(time.time())
                        }
                    )
                except Exception as e:
                    print(f"Error updating execution completion: {e}")
        
        elif failed_count > 0:
            print(f"❌ Wave {wave_number} FAILED - {failed_count} servers failed")
            application['wave_completed'] = True
            application['status'] = 'failed'
            application['error'] = f'{failed_count} servers failed to launch'
            
            # Update DynamoDB with failure
            update_wave_in_dynamodb(execution_id, plan_id, wave_number, 'FAILED', server_statuses)
            
            try:
                get_execution_history_table().update_item(
                    Key={'ExecutionId': execution_id, 'PlanId': plan_id},
                    UpdateExpression='SET #status = :status',
                    ExpressionAttributeNames={'#status': 'Status'},
                    ExpressionAttributeValues={':status': 'FAILED'}
                )
            except Exception as e:
                print(f"Error updating execution failure: {e}")
        
        else:
            print(f"⏳ Wave {wave_number} still in progress - continuing to poll")
            print(f"   Launched: {launched_count}/{total_servers}")
            application['wave_completed'] = False
        
    except Exception as e:
        print(f"Error checking DRS job status: {e}")
        import traceback
        traceback.print_exc()
        application['wave_completed'] = True
        application['status'] = 'failed'
        application['error'] = str(e)
    
    return application


def update_wave_in_dynamodb(execution_id: str, plan_id: str, wave_number: int, 
                            status: str, server_statuses: List[Dict]) -> None:
    """Update wave status in DynamoDB execution record"""
    try:
        exec_response = get_execution_history_table().get_item(
            Key={'ExecutionId': execution_id, 'PlanId': plan_id}
        )
        
        if 'Item' in exec_response:
            execution = exec_response['Item']
            waves = execution.get('Waves', [])
            
            # Update the current wave
            for i, w in enumerate(waves):
                if w.get('WaveNumber') == wave_number:
                    waves[i]['Status'] = status
                    waves[i]['EndTime'] = int(time.time())
                    waves[i]['ServerStatuses'] = server_statuses
                    break
            
            get_execution_history_table().update_item(
                Key={'ExecutionId': execution_id, 'PlanId': plan_id},
                UpdateExpression='SET Waves = :waves',
                ExpressionAttributeValues={':waves': waves}
            )
    except Exception as e:
        print(f"Error updating wave in DynamoDB: {e}")
