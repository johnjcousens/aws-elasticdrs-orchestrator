"""
AWS DRS Orchestration - Orchestration Lambda
Handles Step Functions-driven wave-based recovery execution
"""

import json
import os
import time
import boto3
from typing import Dict, Any, List, Optional
from decimal import Decimal

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
drs = boto3.client('drs')
ec2 = boto3.client('ec2')
ssm = boto3.client('ssm')
sns = boto3.client('sns')
sts = boto3.client('sts')

# Environment variables
PROTECTION_GROUPS_TABLE = os.environ['PROTECTION_GROUPS_TABLE']
RECOVERY_PLANS_TABLE = os.environ['RECOVERY_PLANS_TABLE']
EXECUTION_HISTORY_TABLE = os.environ['EXECUTION_HISTORY_TABLE']
NOTIFICATION_TOPIC_ARN = os.environ.get('NOTIFICATION_TOPIC_ARN', '')

# DynamoDB tables
protection_groups_table = dynamodb.Table(PROTECTION_GROUPS_TABLE)
recovery_plans_table = dynamodb.Table(RECOVERY_PLANS_TABLE)
execution_history_table = dynamodb.Table(EXECUTION_HISTORY_TABLE)


def lambda_handler(event: Dict, context: Any) -> Dict:
    """Main Lambda handler - routes to appropriate action"""
    print(f"Received event: {json.dumps(event, default=str)}")
    
    try:
        action = event.get('action', 'BEGIN')
        
        if action == 'BEGIN':
            return begin_execution(event)
        elif action == 'EXECUTE_WAVE':
            return execute_wave(event)
        elif action == 'UPDATE_WAVE_STATUS':
            return update_wave_status(event)
        elif action == 'EXECUTE_ACTION':
            return execute_action(event)
        elif action == 'UPDATE_ACTION_STATUS':
            return update_action_status(event)
        elif action == 'COMPLETE':
            return complete_execution(event)
        else:
            raise ValueError(f"Unknown action: {action}")
            
    except Exception as e:
        print(f"Error in orchestrator: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


def begin_execution(event: Dict) -> Dict:
    """Initialize execution context and retrieve Recovery Plan"""
    print("Beginning execution...")
    
    plan_id = event['PlanId']
    execution_type = event['ExecutionType']
    initiated_by = event['InitiatedBy']
    
    # Retrieve Recovery Plan
    plan_result = recovery_plans_table.get_item(Key={'PlanId': plan_id})
    if 'Item' not in plan_result:
        raise ValueError(f"Recovery Plan not found: {plan_id}")
    
    plan = plan_result['Item']
    
    # Validate all Protection Groups exist
    for wave in plan['Waves']:
        group_id = wave['ProtectionGroupId']
        group_result = protection_groups_table.get_item(Key={'GroupId': group_id})
        if 'Item' not in group_result:
            raise ValueError(f"Protection Group not found: {group_id}")
    
    # Initialize execution context
    context = {
        'ExecutionId': event.get('ExecutionId', f"exec-{int(time.time())}"),
        'PlanId': plan_id,
        'Plan': convert_decimals(plan),
        'ExecutionType': execution_type,
        'InitiatedBy': initiated_by,
        'TopicArn': event.get('TopicArn', ''),
        'DryRun': event.get('DryRun', False),
        'CurrentWaveIndex': 0,
        'WaveResults': [],
        'Status': 'RUNNING',
        'StartTime': int(time.time())
    }
    
    print(f"Initialized execution context for plan: {plan['PlanName']}")
    return context


def execute_wave(event: Dict) -> Dict:
    """Execute a single wave in the recovery plan"""
    print("Executing wave...")
    
    context = event
    plan = context['Plan']
    current_wave_index = context['CurrentWaveIndex']
    
    if current_wave_index >= len(plan['Waves']):
        context['Status'] = 'COMPLETED'
        return context
    
    wave = plan['Waves'][current_wave_index]
    wave_id = wave['WaveId']
    wave_name = wave['WaveName']
    
    print(f"Executing Wave {current_wave_index + 1}: {wave_name}")
    
    # Check wave dependencies
    if not check_wave_dependencies(wave, context):
        print(f"Wave {wave_name} dependencies not met, waiting...")
        context['WaitingForDependencies'] = True
        return context
    
    # Get Protection Group
    group_id = wave['ProtectionGroupId']
    group_result = protection_groups_table.get_item(Key={'GroupId': group_id})
    if 'Item' not in group_result:
        raise ValueError(f"Protection Group not found: {group_id}")
    
    group = convert_decimals(group_result['Item'])
    
    # Initialize wave result
    wave_result = {
        'WaveId': wave_id,
        'WaveName': wave_name,
        'Status': 'RUNNING',
        'StartTime': int(time.time()),
        'PreWaveActionResults': [],
        'RecoveredInstances': [],
        'PostWaveActionResults': [],
        'Logs': []
    }
    
    # Execute Pre-Wave Actions
    pre_wave_actions = wave.get('PreWaveActions', [])
    for action in pre_wave_actions:
        action_result = execute_automation_action(
            action,
            group,
            context,
            'PreWave'
        )
        wave_result['PreWaveActionResults'].append(action_result)
        
        if action_result['Status'] == 'FAILED':
            wave_result['Status'] = 'FAILED'
            wave_result['EndTime'] = int(time.time())
            context['WaveResults'].append(wave_result)
            context['Status'] = 'FAILED'
            return context
    
    # Start DRS Recovery
    is_drill = context['ExecutionType'] == 'DRILL'
    dry_run = context.get('DryRun', False)
    
    if not dry_run:
        try:
            drs_job_id = start_drs_recovery(
                group['SourceServerIds'],
                is_drill,
                group['AccountId'],
                group['Region']
            )
            
            wave_result['DRSJobId'] = drs_job_id
            wave_result['DRSJobStatus'] = 'PENDING'
            wave_result['Logs'].append(f"Started DRS recovery job: {drs_job_id}")
            print(f"Started DRS recovery job: {drs_job_id}")
        except Exception as e:
            error_msg = f"Failed to start DRS recovery: {str(e)}"
            wave_result['Logs'].append(error_msg)
            wave_result['Status'] = 'FAILED'
            wave_result['EndTime'] = int(time.time())
            context['WaveResults'].append(wave_result)
            context['Status'] = 'FAILED'
            context['ErrorDetails'] = {
                'ErrorType': 'DRSStartFailure',
                'ErrorMessage': str(e),
                'FailedWaveId': wave_id
            }
            return context
    else:
        wave_result['Logs'].append("Dry run mode - skipping DRS recovery")
        print("Dry run mode - skipping actual DRS recovery")
    
    # Add wave result to context
    context['WaveResults'].append(wave_result)
    context['WaveInProgress'] = True
    
    return context


def update_wave_status(event: Dict) -> Dict:
    """Poll DRS job status and update wave progress"""
    print("Updating wave status...")
    
    context = event
    current_wave_index = context['CurrentWaveIndex']
    wave_result = context['WaveResults'][current_wave_index]
    
    plan = context['Plan']
    wave = plan['Waves'][current_wave_index]
    
    # Get Protection Group
    group_id = wave['ProtectionGroupId']
    group_result = protection_groups_table.get_item(Key={'GroupId': group_id})
    group = convert_decimals(group_result['Item'])
    
    # Check if dry run
    if context.get('DryRun', False):
        wave_result['Status'] = 'SUCCEEDED'
        wave_result['EndTime'] = int(time.time())
        wave_result['Logs'].append("Dry run completed successfully")
        context['WaveInProgress'] = False
        context['CurrentWaveIndex'] += 1
        return context
    
    # Poll DRS job status
    drs_job_id = wave_result.get('DRSJobId')
    if not drs_job_id:
        raise ValueError("No DRS Job ID found in wave result")
    
    try:
        drs_client = get_drs_client(group['AccountId'], group['Region'])
        job_response = drs_client.describe_jobs(
            filters={'jobIDs': [drs_job_id]}
        )
        
        if not job_response.get('items'):
            raise ValueError(f"DRS job not found: {drs_job_id}")
        
        job = job_response['items'][0]
        job_status = job['status']
        wave_result['DRSJobStatus'] = job_status
        
        print(f"DRS Job status: {job_status}")
        
        if job_status == 'COMPLETED':
            # Get recovered instances
            participating_servers = job.get('participatingServers', [])
            recovered_instances = []
            
            for ps in participating_servers:
                source_server_id = ps.get('sourceServerID')
                launched_instance_id = ps.get('launchedEC2InstanceID')
                
                if launched_instance_id:
                    # Get instance details
                    ec2_response = ec2.describe_instances(
                        InstanceIds=[launched_instance_id]
                    )
                    
                    if ec2_response['Reservations']:
                        instance = ec2_response['Reservations'][0]['Instances'][0]
                        recovered_instances.append({
                            'SourceServerId': source_server_id,
                            'RecoveredInstanceId': launched_instance_id,
                            'RecoveredInstanceState': instance['State']['Name'],
                            'LaunchTime': int(time.time()),
                            'PrivateIpAddress': instance.get('PrivateIpAddress', ''),
                            'PublicIpAddress': instance.get('PublicIpAddress', '')
                        })
            
            wave_result['RecoveredInstances'] = recovered_instances
            wave_result['Logs'].append(f"Recovered {len(recovered_instances)} instances")
            
            # Execute Post-Wave Actions
            post_wave_actions = wave.get('PostWaveActions', [])
            for action in post_wave_actions:
                action_result = execute_automation_action(
                    action,
                    group,
                    context,
                    'PostWave',
                    recovered_instances
                )
                wave_result['PostWaveActionResults'].append(action_result)
                
                if action_result['Status'] == 'FAILED':
                    wave_result['Status'] = 'FAILED'
                    wave_result['EndTime'] = int(time.time())
                    context['WaveInProgress'] = False
                    context['Status'] = 'FAILED'
                    return context
            
            # Wave completed successfully
            wave_result['Status'] = 'SUCCEEDED'
            wave_result['EndTime'] = int(time.time())
            wave_result['Duration'] = wave_result['EndTime'] - wave_result['StartTime']
            wave_result['Logs'].append("Wave completed successfully")
            
            context['WaveInProgress'] = False
            context['CurrentWaveIndex'] += 1
            
        elif job_status in ['FAILED', 'TERMINATED']:
            wave_result['Status'] = 'FAILED'
            wave_result['EndTime'] = int(time.time())
            wave_result['Logs'].append(f"DRS job failed with status: {job_status}")
            context['WaveInProgress'] = False
            context['Status'] = 'FAILED'
            context['ErrorDetails'] = {
                'ErrorType': 'DRSJobFailure',
                'ErrorMessage': f"DRS job {drs_job_id} failed",
                'FailedWaveId': wave['WaveId']
            }
        else:
            # Still in progress
            wave_result['Logs'].append(f"DRS job in progress: {job_status}")
            context['WaitingForJob'] = True
            
    except Exception as e:
        error_msg = f"Error checking DRS job status: {str(e)}"
        wave_result['Logs'].append(error_msg)
        wave_result['Status'] = 'FAILED'
        wave_result['EndTime'] = int(time.time())
        context['WaveInProgress'] = False
        context['Status'] = 'FAILED'
        context['ErrorDetails'] = {
            'ErrorType': 'DRSStatusCheckFailure',
            'ErrorMessage': str(e),
            'FailedWaveId': wave['WaveId']
        }
    
    return context


def execute_action(event: Dict) -> Dict:
    """Execute a single automation action"""
    print("Executing action...")
    # Implementation would be similar to execute_automation_action
    # but designed to work with Step Functions Tasks
    return event


def update_action_status(event: Dict) -> Dict:
    """Update status of a running automation action"""
    print("Updating action status...")
    # Implementation would poll SSM for automation status
    return event


def complete_execution(event: Dict) -> Dict:
    """Finalize execution and update history"""
    print("Completing execution...")
    
    context = event
    execution_id = context['ExecutionId']
    plan_id = context['PlanId']
    
    # Calculate final status
    if context['Status'] == 'RUNNING':
        context['Status'] = 'SUCCEEDED'
    
    context['EndTime'] = int(time.time())
    context['Duration'] = context['EndTime'] - context['StartTime']
    
    # Update execution history in DynamoDB
    history_item = {
        'ExecutionId': execution_id,
        'PlanId': plan_id,
        'ExecutionType': context['ExecutionType'],
        'Status': context['Status'],
        'StartTime': context['StartTime'],
        'EndTime': context['EndTime'],
        'Duration': context['Duration'],
        'InitiatedBy': context['InitiatedBy'],
        'TopicArn': context.get('TopicArn', ''),
        'WaveResults': context['WaveResults']
    }
    
    if 'ErrorDetails' in context:
        history_item['ErrorDetails'] = context['ErrorDetails']
    
    execution_history_table.put_item(Item=history_item)
    
    # Send notification if topic ARN provided
    if context.get('TopicArn'):
        send_execution_notification(
            execution_id,
            context['Status'],
            context['TopicArn'],
            context
        )
    
    print(f"Execution completed with status: {context['Status']}")
    return context


# ============================================================================
# Helper Functions
# ============================================================================

def check_wave_dependencies(wave: Dict, context: Dict) -> bool:
    """Check if all wave dependencies are met"""
    dependencies = wave.get('Dependencies', [])
    
    if not dependencies:
        return True
    
    wave_results = context.get('WaveResults', [])
    
    for dependency in dependencies:
        depends_on_wave_id = dependency['DependsOnWaveId']
        condition_type = dependency.get('ConditionType', 'COMPLETE')
        
        # Find the dependent wave result
        dependent_result = None
        for result in wave_results:
            if result['WaveId'] == depends_on_wave_id:
                dependent_result = result
                break
        
        if not dependent_result:
            print(f"Dependent wave {depends_on_wave_id} has not started yet")
            return False
        
        if condition_type == 'COMPLETE':
            if dependent_result['Status'] != 'SUCCEEDED':
                print(f"Dependent wave {depends_on_wave_id} not completed")
                return False
        
        elif condition_type == 'RUNNING':
            if dependent_result['Status'] not in ['RUNNING', 'SUCCEEDED']:
                print(f"Dependent wave {depends_on_wave_id} not running")
                return False
        
        elif condition_type == 'HEALTHY':
            if dependent_result['Status'] != 'SUCCEEDED':
                return False
            
            # Check instance health if specified
            instance_id = dependency.get('InstanceId')
            if instance_id:
                if not check_instance_health(instance_id, dependency.get('HealthCheckType')):
                    print(f"Instance {instance_id} health check failed")
                    return False
    
    return True


def check_instance_health(instance_id: str, health_check_type: Optional[str]) -> bool:
    """Check EC2 instance health"""
    try:
        if not health_check_type or health_check_type == 'STATUS_CHECK':
            response = ec2.describe_instance_status(InstanceIds=[instance_id])
            
            if not response['InstanceStatuses']:
                return False
            
            status = response['InstanceStatuses'][0]
            instance_status = status['InstanceStatus']['Status']
            system_status = status['SystemStatus']['Status']
            
            return instance_status == 'ok' and system_status == 'ok'
        
        # Custom script health check would be implemented here
        return True
        
    except Exception as e:
        print(f"Error checking instance health: {str(e)}")
        return False


def execute_automation_action(
    action: Dict,
    group: Dict,
    context: Dict,
    action_phase: str,
    recovered_instances: Optional[List[Dict]] = None
) -> Dict:
    """Execute an SSM automation action"""
    action_result = {
        'ActionId': action['ActionId'],
        'ActionName': action['ActionName'],
        'Status': 'RUNNING',
        'StartTime': int(time.time())
    }
    
    try:
        action_type = action['ActionType']
        
        if action_type == 'SSM_DOCUMENT':
            ssm_doc = action.get('SSMDocument', {})
            doc_name = ssm_doc['DocumentName']
            parameters = ssm_doc.get('Parameters', {})
            
            # Determine targets
            targets = []
            target_type = ssm_doc.get('TargetType', 'RECOVERED_INSTANCE')
            
            if target_type == 'RECOVERED_INSTANCE' and recovered_instances:
                instance_ids = [ri['RecoveredInstanceId'] for ri in recovered_instances]
                targets = [{'Key': 'InstanceIds', 'Values': instance_ids}]
            
            elif target_type == 'TAG':
                targets = [{
                    'Key': f'tag:{ssm_doc["TargetKey"]}',
                    'Values': [ssm_doc['TargetValue']]
                }]
            
            # Start SSM automation
            ssm_response = ssm.start_automation_execution(
                DocumentName=doc_name,
                Parameters=parameters,
                Targets=targets if targets else None
            )
            
            action_result['SSMExecutionId'] = ssm_response['AutomationExecutionId']
            action_result['SSMExecutionStatus'] = 'InProgress'
            
            # Poll for completion (simplified - in production would use Step Functions Wait)
            max_wait = action.get('MaxWaitTime', 300)
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                status_response = ssm.describe_automation_executions(
                    Filters=[{
                        'Key': 'ExecutionId',
                        'Values': [ssm_response['AutomationExecutionId']]
                    }]
                )
                
                if status_response['AutomationExecutionMetadataList']:
                    exec_status = status_response['AutomationExecutionMetadataList'][0]['AutomationExecutionStatus']
                    action_result['SSMExecutionStatus'] = exec_status
                    
                    if exec_status == 'Success':
                        action_result['Status'] = 'SUCCEEDED'
                        break
                    elif exec_status in ['Failed', 'TimedOut', 'Cancelled']:
                        action_result['Status'] = 'FAILED'
                        action_result['ErrorMessage'] = f"SSM execution {exec_status}"
                        break
                
                time.sleep(5)
            
            if action_result['Status'] == 'RUNNING':
                action_result['Status'] = 'TIMEOUT'
                action_result['ErrorMessage'] = 'Action timed out'
        
        elif action_type == 'WAIT':
            wait_seconds = action.get('MaxWaitTime', 60)
            time.sleep(min(wait_seconds, 30))  # Cap at 30s for Lambda
            action_result['Status'] = 'SUCCEEDED'
        
        action_result['EndTime'] = int(time.time())
        action_result['Duration'] = action_result['EndTime'] - action_result['StartTime']
        
    except Exception as e:
        action_result['Status'] = 'FAILED'
        action_result['ErrorMessage'] = str(e)
        action_result['EndTime'] = int(time.time())
        print(f"Error executing action {action['ActionName']}: {str(e)}")
    
    return action_result


def start_drs_recovery(
    source_server_ids: List[str],
    is_drill: bool,
    account_id: str,
    region: str
) -> str:
    """Start DRS recovery job"""
    try:
        drs_client = get_drs_client(account_id, region)
        
        response = drs_client.start_recovery(
            isDrill=is_drill,
            sourceServers=[{'sourceServerID': sid} for sid in source_server_ids]
        )
        
        job_id = response['job']['jobID']
        return job_id
        
    except Exception as e:
        print(f"Error starting DRS recovery: {str(e)}")
        raise


def get_drs_client(account_id: str, region: str):
    """Get DRS client with cross-account role assumption if needed"""
    # For now, use current credentials
    # In production, would check if account_id differs from current account
    # and assume cross-account role if needed
    return boto3.client('drs', region_name=region)


def send_execution_notification(
    execution_id: str,
    status: str,
    topic_arn: str,
    context: Dict
):
    """Send SNS notification about execution status"""
    try:
        plan = context['Plan']
        
        message = f"""
DRS Orchestration Execution {status}

Execution ID: {execution_id}
Recovery Plan: {plan['PlanName']}
Execution Type: {context['ExecutionType']}
Status: {status}
Duration: {context.get('Duration', 0)} seconds

Waves Executed: {len(context['WaveResults'])}
"""
        
        if status == 'FAILED' and 'ErrorDetails' in context:
            error = context['ErrorDetails']
            message += f"\nError: {error.get('ErrorMessage', 'Unknown error')}"
        
        sns.publish(
            TopicArn=topic_arn,
            Subject=f"DRS Orchestration: {plan['PlanName']} - {status}",
            Message=message
        )
        
        print(f"Sent notification to {topic_arn}")
        
    except Exception as e:
        print(f"Error sending notification: {str(e)}")


def convert_decimals(obj):
    """Convert DynamoDB Decimal types to int/float"""
    if isinstance(obj, list):
        return [convert_decimals(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    else:
        return obj
