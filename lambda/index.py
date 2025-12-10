"""
AWS DRS Orchestration - API Handler Lambda
Handles REST API requests for Protection Groups, Recovery Plans, and Executions
"""

import json
import os
import uuid
import time
from datetime import datetime, timezone
import boto3
from boto3.dynamodb.conditions import Key, Attr
from decimal import Decimal
from typing import Dict, Any, List, Optional

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
stepfunctions = boto3.client('stepfunctions')
drs = boto3.client('drs')
lambda_client = boto3.client('lambda')

# Environment variables
PROTECTION_GROUPS_TABLE = os.environ['PROTECTION_GROUPS_TABLE']
RECOVERY_PLANS_TABLE = os.environ['RECOVERY_PLANS_TABLE']
EXECUTION_HISTORY_TABLE = os.environ['EXECUTION_HISTORY_TABLE']
STATE_MACHINE_ARN = os.environ.get('STATE_MACHINE_ARN', '')

# DynamoDB tables
protection_groups_table = dynamodb.Table(PROTECTION_GROUPS_TABLE)
recovery_plans_table = dynamodb.Table(RECOVERY_PLANS_TABLE)
execution_history_table = dynamodb.Table(EXECUTION_HISTORY_TABLE)


def get_cognito_user_from_event(event: Dict) -> Dict:
    """Extract Cognito user info from API Gateway authorizer"""
    try:
        authorizer = event.get('requestContext', {}).get('authorizer', {})
        claims = authorizer.get('claims', {})
        return {
            'email': claims.get('email', 'system'),
            'userId': claims.get('sub', 'system'),
            'username': claims.get('cognito:username', 'system')
        }
    except Exception as e:
        print(f"Error extracting Cognito user: {e}")
        return {'email': 'system', 'userId': 'system', 'username': 'system'}


class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder for DynamoDB Decimal types"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super(DecimalEncoder, self).default(obj)


def response(status_code: int, body: Any, headers: Optional[Dict] = None) -> Dict:
    """Generate API Gateway response with CORS headers"""
    default_headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
    }
    if headers:
        default_headers.update(headers)
    
    return {
        'statusCode': status_code,
        'headers': default_headers,
        'body': json.dumps(body, cls=DecimalEncoder)
    }


# ============================================================================
# Conflict Detection Helpers
# ============================================================================

# Active execution statuses that indicate an execution is still running
ACTIVE_EXECUTION_STATUSES = ['PENDING', 'POLLING', 'INITIATED', 'LAUNCHING', 'STARTED', 
                             'IN_PROGRESS', 'RUNNING', 'PAUSED', 'CANCELLING']


def get_active_executions_for_plan(plan_id: str) -> List[Dict]:
    """Get all active executions for a specific recovery plan"""
    try:
        # Try GSI first
        try:
            result = execution_history_table.query(
                IndexName='PlanIdIndex',
                KeyConditionExpression=Key('PlanId').eq(plan_id)
            )
            executions = result.get('Items', [])
        except Exception:
            # Fallback to scan
            result = execution_history_table.scan(
                FilterExpression=Attr('PlanId').eq(plan_id)
            )
            executions = result.get('Items', [])
        
        # Filter to active statuses
        return [e for e in executions if e.get('Status', '').upper() in ACTIVE_EXECUTION_STATUSES]
    except Exception as e:
        print(f"Error checking active executions for plan {plan_id}: {e}")
        return []


def get_active_execution_for_protection_group(group_id: str) -> Optional[Dict]:
    """
    Check if a protection group is part of any active execution.
    Returns execution info if found, None otherwise.
    """
    try:
        # First, find all recovery plans that use this protection group
        plans_result = recovery_plans_table.scan()
        all_plans = plans_result.get('Items', [])
        
        # Handle pagination
        while 'LastEvaluatedKey' in plans_result:
            plans_result = recovery_plans_table.scan(
                ExclusiveStartKey=plans_result['LastEvaluatedKey']
            )
            all_plans.extend(plans_result.get('Items', []))
        
        # Find plan IDs that reference this protection group
        plan_ids_with_pg = []
        for plan in all_plans:
            for wave in plan.get('Waves', []):
                pg_id_in_wave = wave.get('ProtectionGroupId')
                if pg_id_in_wave == group_id:
                    plan_ids_with_pg.append(plan.get('PlanId'))
                    break
        
        if not plan_ids_with_pg:
            return None  # PG not used in any plan
        
        # Check if any of these plans have active executions
        for plan_id in plan_ids_with_pg:
            active_executions = get_active_executions_for_plan(plan_id)
            if active_executions:
                exec_info = active_executions[0]
                # Get plan name
                plan = next((p for p in all_plans if p.get('PlanId') == plan_id), {})
                return {
                    'executionId': exec_info.get('ExecutionId'),
                    'planId': plan_id,
                    'planName': plan.get('PlanName', 'Unknown'),
                    'status': exec_info.get('Status')
                }
        
        return None
    except Exception as e:
        print(f"Error checking active execution for protection group: {e}")
        return None


def get_all_active_executions() -> List[Dict]:
    """Get all active executions across all plans"""
    try:
        # Try StatusIndex GSI first
        active_executions = []
        for status in ACTIVE_EXECUTION_STATUSES:
            try:
                result = execution_history_table.query(
                    IndexName='StatusIndex',
                    KeyConditionExpression=Key('Status').eq(status)
                )
                active_executions.extend(result.get('Items', []))
            except Exception:
                pass  # GSI might not exist for all statuses
        
        # If no results from GSI, fallback to scan
        if not active_executions:
            result = execution_history_table.scan()
            all_executions = result.get('Items', [])
            active_executions = [e for e in all_executions 
                                if e.get('Status', '').upper() in ACTIVE_EXECUTION_STATUSES]
        
        return active_executions
    except Exception as e:
        print(f"Error getting all active executions: {e}")
        return []


def get_servers_in_active_executions() -> Dict[str, Dict]:
    """
    Get all servers currently in active executions.
    Returns dict mapping server_id -> {execution_id, plan_id, wave_name, status}
    
    IMPORTANT: For PAUSED executions, we must look up the original Recovery Plan
    to get ALL servers that will be affected when the execution resumes,
    not just the waves already recorded in the execution history.
    """
    active_executions = get_all_active_executions()
    servers_in_use = {}
    
    # Cache for recovery plans to avoid repeated lookups
    plan_cache = {}
    
    for execution in active_executions:
        execution_id = execution.get('ExecutionId')
        plan_id = execution.get('PlanId')
        exec_status = execution.get('Status', '').upper()
        
        # For PAUSED or PENDING executions, get ALL servers from the original Recovery Plan
        # because they will be affected when the execution resumes
        if exec_status in ['PAUSED', 'PENDING', 'PAUSE_PENDING']:
            # Look up the original Recovery Plan
            if plan_id not in plan_cache:
                try:
                    plan_result = recovery_plans_table.get_item(Key={'PlanId': plan_id})
                    plan_cache[plan_id] = plan_result.get('Item', {})
                except Exception as e:
                    print(f"Error fetching plan {plan_id}: {e}")
                    plan_cache[plan_id] = {}
            
            plan = plan_cache.get(plan_id, {})
            paused_before_wave = execution.get('PausedBeforeWave', 1)
            
            # Convert Decimal to int if needed
            if hasattr(paused_before_wave, '__int__'):
                paused_before_wave = int(paused_before_wave)
            
            # Get all servers from waves that haven't completed yet
            for idx, wave in enumerate(plan.get('Waves', []), start=1):
                wave_name = wave.get('WaveName', f'Wave {idx}')
                
                # For PAUSED: include servers from paused wave onwards
                # For PENDING: include all servers
                if exec_status == 'PENDING' or idx >= paused_before_wave:
                    for server_id in wave.get('ServerIds', []):
                        servers_in_use[server_id] = {
                            'executionId': execution_id,
                            'planId': plan_id,
                            'waveName': wave_name,
                            'waveStatus': 'PENDING (paused)' if exec_status == 'PAUSED' else 'PENDING',
                            'executionStatus': exec_status
                        }
        
        # For running executions, check the waves in the execution record
        # Get servers from waves that are active or pending
        for wave in execution.get('Waves', []):
            wave_name = wave.get('WaveName', 'Unknown')
            wave_status = wave.get('Status', '')
            
            # Only consider waves that are active or pending
            if wave_status.upper() in ['PENDING', 'STARTED', 'IN_PROGRESS', 'POLLING', 'LAUNCHING']:
                for server_id in wave.get('ServerIds', []):
                    servers_in_use[server_id] = {
                        'executionId': execution_id,
                        'planId': plan_id,
                        'waveName': wave_name,
                        'waveStatus': wave_status,
                        'executionStatus': exec_status
                    }
        
        # Also check ServerStatuses if present
        for wave in execution.get('Waves', []):
            wave_name = wave.get('WaveName', 'Unknown')
            for server in wave.get('ServerStatuses', []):
                server_id = server.get('SourceServerId')
                launch_status = server.get('LaunchStatus', '')
                # Only track servers not yet launched
                if server_id and launch_status.upper() not in ['LAUNCHED', 'FAILED', 'TERMINATED']:
                    servers_in_use[server_id] = {
                        'executionId': execution_id,
                        'planId': plan_id,
                        'waveName': wave_name,
                        'launchStatus': launch_status,
                        'executionStatus': exec_status
                    }
    
    return servers_in_use


def check_server_conflicts(plan: Dict) -> List[Dict]:
    """
    Check if any servers in the plan are currently in active executions.
    Returns list of conflicts with details.
    """
    servers_in_use = get_servers_in_active_executions()
    conflicts = []
    
    for wave in plan.get('Waves', []):
        wave_name = wave.get('WaveName', 'Unknown')
        for server_id in wave.get('ServerIds', []):
            if server_id in servers_in_use:
                conflict_info = servers_in_use[server_id]
                conflicts.append({
                    'serverId': server_id,
                    'waveName': wave_name,
                    'conflictingExecutionId': conflict_info['executionId'],
                    'conflictingPlanId': conflict_info['planId'],
                    'conflictingWaveName': conflict_info.get('waveName'),
                    'conflictingStatus': conflict_info.get('executionStatus')
                })
    
    return conflicts


def get_plans_with_conflicts() -> Dict[str, Dict]:
    """
    Get all recovery plans that have server conflicts with active executions.
    Returns dict mapping plan_id -> conflict info for plans that cannot be executed.
    
    This is used by the frontend to gray out Drill/Recovery buttons.
    """
    servers_in_use = get_servers_in_active_executions()
    
    if not servers_in_use:
        return {}
    
    # Get all recovery plans
    try:
        result = recovery_plans_table.scan()
        all_plans = result.get('Items', [])
        
        # Handle pagination
        while 'LastEvaluatedKey' in result:
            result = recovery_plans_table.scan(
                ExclusiveStartKey=result['LastEvaluatedKey']
            )
            all_plans.extend(result.get('Items', []))
    except Exception as e:
        print(f"Error fetching plans for conflict check: {e}")
        return {}
    
    plans_with_conflicts = {}
    
    for plan in all_plans:
        plan_id = plan.get('PlanId')
        
        # Check if this plan has any servers in active executions
        conflicting_servers = []
        conflicting_execution_id = None
        conflicting_plan_id = None
        conflicting_status = None
        
        for wave in plan.get('Waves', []):
            for server_id in wave.get('ServerIds', []):
                if server_id in servers_in_use:
                    conflict_info = servers_in_use[server_id]
                    # Don't count as conflict if it's this plan's own execution
                    if conflict_info['planId'] != plan_id:
                        conflicting_servers.append(server_id)
                        conflicting_execution_id = conflict_info['executionId']
                        conflicting_plan_id = conflict_info['planId']
                        conflicting_status = conflict_info.get('executionStatus')
        
        if conflicting_servers:
            plans_with_conflicts[plan_id] = {
                'hasConflict': True,
                'conflictingServers': conflicting_servers,
                'conflictingExecutionId': conflicting_execution_id,
                'conflictingPlanId': conflicting_plan_id,
                'conflictingStatus': conflicting_status,
                'reason': f'{len(conflicting_servers)} server(s) in use by another execution'
            }
    
    return plans_with_conflicts


def lambda_handler(event: Dict, context: Any) -> Dict:
    """Main Lambda handler - routes requests to appropriate functions"""
    print(f"Received event: {json.dumps(event)}")
    
    try:
        # Check if this is a worker invocation (async execution)
        if event.get('worker'):
            print("Worker mode detected - executing background task")
            execute_recovery_plan_worker(event)
            return {'statusCode': 200, 'body': 'Worker completed'}
        
        # Normal API Gateway request handling
        http_method = event.get('httpMethod', '')
        path = event.get('path', '')
        path_parameters = event.get('pathParameters') or {}
        query_parameters = event.get('queryStringParameters') or {}
        body = json.loads(event.get('body', '{}')) if event.get('body') else {}
        
        # Handle OPTIONS requests for CORS
        if http_method == 'OPTIONS':
            return response(200, {'message': 'OK'})
        
        # Route to appropriate handler
        if path.startswith('/protection-groups'):
            return handle_protection_groups(http_method, path_parameters, body)
        elif '/execute' in path and path.startswith('/recovery-plans'):
            # Handle /recovery-plans/{planId}/execute endpoint
            plan_id = path_parameters.get('id')
            body['PlanId'] = plan_id
            if 'InitiatedBy' not in body:
                body['InitiatedBy'] = 'system'
            return execute_recovery_plan(body)
        elif path.startswith('/recovery-plans'):
            return handle_recovery_plans(http_method, path_parameters, body)
        elif path.startswith('/executions'):
            # Pass full path for action routing (cancel, pause, resume)
            path_parameters['_full_path'] = path
            return handle_executions(http_method, path_parameters, query_parameters, body)
        elif path.startswith('/drs/source-servers'):
            return handle_drs_source_servers(query_parameters)
        else:
            return response(404, {'error': 'Not Found', 'path': path})
            
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return response(500, {'error': 'Internal Server Error', 'message': str(e)})


# ============================================================================
# Protection Groups Handlers
# ============================================================================

def handle_protection_groups(method: str, path_params: Dict, body: Dict) -> Dict:
    """Route Protection Groups requests"""
    group_id = path_params.get('id')
    
    if method == 'POST':
        return create_protection_group(body)
    elif method == 'GET' and not group_id:
        return get_protection_groups()
    elif method == 'GET' and group_id:
        return get_protection_group(group_id)
    elif method == 'PUT' and group_id:
        return update_protection_group(group_id, body)
    elif method == 'DELETE' and group_id:
        return delete_protection_group(group_id)
    else:
        return response(405, {'error': 'Method Not Allowed'})


def create_protection_group(body: Dict) -> Dict:
    """Create a new Protection Group with automatic server discovery"""
    try:
        # Validate required fields for new schema
        if 'GroupName' not in body:
            return response(400, {'error': 'GroupName is required'})
        
        if 'Region' not in body:
            return response(400, {'error': 'Region is required'})
        
        if 'sourceServerIds' not in body or not body['sourceServerIds']:
            return response(400, {'error': 'At least one source server must be selected'})
        
        name = body['GroupName']
        server_ids = body['sourceServerIds']
        region = body['Region']
        
        # NEW: Validate servers exist in DRS (CRITICAL - prevents fake data)
        invalid_servers = validate_servers_exist_in_drs(region, server_ids)
        if invalid_servers:
            return response(400, {
                'error': 'INVALID_SERVER_IDS',
                'message': f'{len(invalid_servers)} server ID(s) do not exist in DRS',
                'invalidServers': invalid_servers,
                'region': region
            })
        
        # Validate unique name (case-insensitive, global across all users)
        if not validate_unique_pg_name(name):
            return response(409, {  # Conflict
                'error': 'PG_NAME_EXISTS',
                'message': f'A Protection Group named "{name}" already exists',
                'existingName': name
            })
        
        # Validate server assignments (no conflicts across all users)
        conflicts = validate_server_assignments(server_ids)
        if conflicts:
            return response(409, {  # Conflict
                'error': 'SERVER_ASSIGNMENT_CONFLICT',
                'message': 'Some servers are already assigned to other Protection Groups',
                'conflicts': conflicts
            })
        
        # Generate UUID for GroupId
        group_id = str(uuid.uuid4())
        
        # Create Protection Group with new schema
        timestamp = int(time.time())
        
        # Validate timestamp is not 0 or negative
        if timestamp <= 0:
            print(f"WARNING: Invalid timestamp generated: {timestamp}")
            timestamp = int(time.time())  # Retry
            if timestamp <= 0:
                raise Exception("Failed to generate valid timestamp")
        
        item = {
            'GroupId': group_id,
            'GroupName': name,
            'Description': body.get('Description', ''),
            'Region': body['Region'],
            'SourceServerIds': server_ids,
            'AccountId': body.get('AccountId', ''),
            'Owner': body.get('Owner', ''),
            'CreatedDate': timestamp,
            'LastModifiedDate': timestamp
        }
        
        print(f"Creating Protection Group with timestamp: {timestamp} ({time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(timestamp))} UTC)")
        
        # Store in DynamoDB
        protection_groups_table.put_item(Item=item)
        
        # Transform to camelCase for frontend
        response_item = transform_pg_to_camelcase(item)
        
        print(f"Created Protection Group: {group_id} with {len(server_ids)} servers")
        return response(201, response_item)
        
    except Exception as e:
        print(f"Error creating Protection Group: {str(e)}")
        import traceback
        traceback.print_exc()
        return response(500, {'error': str(e)})


def get_protection_groups() -> Dict:
    """List all Protection Groups"""
    try:
        result = protection_groups_table.scan()
        groups = result.get('Items', [])
        
        # Transform to camelCase and enrich with current DRS source server status
        camelcase_groups = []
        for group in groups:
            # Only enrich if AccountId is present
            if group.get('AccountId') and group.get('SourceServerIds'):
                try:
                    server_details = get_drs_source_server_details(
                        group['AccountId'],
                        group['Region'],
                        group['SourceServerIds']
                    )
                    group['ServerDetails'] = server_details
                except Exception as e:
                    print(f"Error enriching group {group['GroupId']}: {str(e)}")
                    group['ServerDetails'] = []
            else:
                # Skip enrichment if AccountId is missing
                group['ServerDetails'] = []
            
            # Transform to camelCase
            camelcase_groups.append(transform_pg_to_camelcase(group))
        
        return response(200, {'groups': camelcase_groups, 'count': len(camelcase_groups)})
        
    except Exception as e:
        print(f"Error listing Protection Groups: {str(e)}")
        return response(500, {'error': str(e)})


def get_protection_group(group_id: str) -> Dict:
    """Get a single Protection Group by ID"""
    try:
        result = protection_groups_table.get_item(Key={'GroupId': group_id})
        
        if 'Item' not in result:
            return response(404, {'error': 'Protection Group not found'})
        
        group = result['Item']
        
        # Enrich with DRS source server details
        try:
            server_details = get_drs_source_server_details(
                group['AccountId'],
                group['Region'],
                group['SourceServerIds']
            )
            group['ServerDetails'] = server_details
        except Exception as e:
            print(f"Error enriching group: {str(e)}")
            group['ServerDetails'] = []
        
        # Transform to camelCase
        camelcase_group = transform_pg_to_camelcase(group)
        
        return response(200, camelcase_group)
        
    except Exception as e:
        print(f"Error getting Protection Group: {str(e)}")
        return response(500, {'error': str(e)})


def update_protection_group(group_id: str, body: Dict) -> Dict:
    """Update an existing Protection Group with validation"""
    try:
        # Check if group exists
        result = protection_groups_table.get_item(Key={'GroupId': group_id})
        if 'Item' not in result:
            return response(404, {'error': 'Protection Group not found'})
        
        existing_group = result['Item']
        
        # BLOCK: Cannot update protection group if it's part of an active execution
        active_exec_info = get_active_execution_for_protection_group(group_id)
        if active_exec_info:
            return response(409, {
                'error': 'PG_IN_ACTIVE_EXECUTION',
                'message': f'Cannot modify Protection Group while it is part of an active execution',
                'activeExecution': active_exec_info
            })
        
        # Prevent region changes
        if 'Region' in body and body['Region'] != existing_group.get('Region'):
            return response(400, {'error': 'Cannot change region after creation'})
        
        # Validate unique name if changing
        if 'GroupName' in body and body['GroupName'] != existing_group.get('GroupName'):
            if not validate_unique_pg_name(body['GroupName'], group_id):
                return response(409, {
                    'error': 'PG_NAME_EXISTS',
                    'message': f'A Protection Group named "{body["GroupName"]}" already exists'
                })
        
        # If updating server list, validate they exist in DRS first
        if 'sourceServerIds' in body:
            # NEW: Validate servers exist in DRS
            invalid_servers = validate_servers_exist_in_drs(existing_group['Region'], body['sourceServerIds'])
            if invalid_servers:
                return response(400, {
                    'error': 'INVALID_SERVER_IDS',
                    'message': f'{len(invalid_servers)} server ID(s) do not exist in DRS',
                    'invalidServers': invalid_servers,
                    'region': existing_group['Region']
                })
            
            # Then validate assignments
            conflicts = validate_server_assignments(body['sourceServerIds'], current_pg_id=group_id)
            if conflicts:
                return response(409, {
                    'error': 'SERVER_ASSIGNMENT_CONFLICT',
                    'message': 'Some servers are already assigned to other Protection Groups',
                    'conflicts': conflicts
                })
        
        # Build update expression
        update_expression = "SET LastModifiedDate = :timestamp"
        expression_values = {':timestamp': int(time.time())}
        expression_names = {}
        
        if 'GroupName' in body:
            update_expression += ", GroupName = :name"
            expression_values[':name'] = body['GroupName']
        
        if 'Description' in body:
            update_expression += ", #desc = :desc"
            expression_values[':desc'] = body['Description']
            expression_names['#desc'] = 'Description'
        
        if 'sourceServerIds' in body:
            update_expression += ", SourceServerIds = :servers"
            expression_values[':servers'] = body['sourceServerIds']
        
        # Legacy support for Tags (if present, ignore - new schema doesn't use them)
        if 'Tags' in body:
            print(f"Warning: Tags field ignored in update (legacy field)")
        
        # Update item
        update_args = {
            'Key': {'GroupId': group_id},
            'UpdateExpression': update_expression,
            'ExpressionAttributeValues': expression_values,
            'ReturnValues': 'ALL_NEW'
        }
        
        if expression_names:
            update_args['ExpressionAttributeNames'] = expression_names
        
        result = protection_groups_table.update_item(**update_args)
        
        print(f"Updated Protection Group: {group_id}")
        return response(200, result['Attributes'])
        
    except Exception as e:
        print(f"Error updating Protection Group: {str(e)}")
        import traceback
        traceback.print_exc()
        return response(500, {'error': str(e)})


def delete_protection_group(group_id: str) -> Dict:
    """Delete a Protection Group - blocked if used in ANY recovery plan"""
    try:
        # Check if group is referenced in ANY Recovery Plans (not just active ones)
        # Scan all plans and check if any wave references this PG
        plans_result = recovery_plans_table.scan()
        all_plans = plans_result.get('Items', [])
        
        # Handle pagination
        while 'LastEvaluatedKey' in plans_result:
            plans_result = recovery_plans_table.scan(
                ExclusiveStartKey=plans_result['LastEvaluatedKey']
            )
            all_plans.extend(plans_result.get('Items', []))
        
        # Find plans that reference this protection group
        referencing_plans = []
        for plan in all_plans:
            for wave in plan.get('Waves', []):
                if wave.get('ProtectionGroupId') == group_id:
                    referencing_plans.append({
                        'planId': plan.get('PlanId'),
                        'planName': plan.get('PlanName'),
                        'waveName': wave.get('WaveName')
                    })
                    break  # Only need to find one wave per plan
        
        if referencing_plans:
            plan_names = list(set([p['planName'] for p in referencing_plans]))
            return response(409, {
                'error': 'PG_IN_USE',
                'message': f'Cannot delete Protection Group - it is used in {len(plan_names)} Recovery Plan(s)',
                'plans': plan_names,
                'details': referencing_plans
            })
        
        # Delete the group
        protection_groups_table.delete_item(Key={'GroupId': group_id})
        
        print(f"Deleted Protection Group: {group_id}")
        return response(200, {'message': 'Protection Group deleted successfully'})
        
    except Exception as e:
        print(f"Error deleting Protection Group: {str(e)}")
        return response(500, {'error': str(e)})


# ============================================================================
# Recovery Plans Handlers
# ============================================================================

def handle_recovery_plans(method: str, path_params: Dict, body: Dict) -> Dict:
    """Route Recovery Plans requests"""
    plan_id = path_params.get('id')
    path = path_params.get('proxy', '')
    
    # Handle /recovery-plans/{planId}/execute endpoint
    if method == 'POST' and plan_id and 'execute' in path:
        # Transform body for execute_recovery_plan
        body['PlanId'] = plan_id
        # Get InitiatedBy from Cognito if not provided
        if 'InitiatedBy' not in body:
            body['InitiatedBy'] = 'system'  # Will be replaced by Cognito user
        return execute_recovery_plan(body)

    if method == 'POST':
        return create_recovery_plan(body)
    elif method == 'GET' and not plan_id:
        return get_recovery_plans()
    elif method == 'GET' and plan_id:
        return get_recovery_plan(plan_id)
    elif method == 'PUT' and plan_id:
        return update_recovery_plan(plan_id, body)
    elif method == 'DELETE' and plan_id:
        return delete_recovery_plan(plan_id)
    else:
        return response(405, {'error': 'Method Not Allowed'})


def create_recovery_plan(body: Dict) -> Dict:
    """Create a new Recovery Plan"""
    try:
        # Validate required fields
        if 'PlanName' not in body:
            return response(400, {'error': 'Missing required field: PlanName'})
        
        if 'Waves' not in body or not body['Waves']:
            return response(400, {'error': 'At least one Wave is required'})
        
        # Validate unique name (case-insensitive, global across all users)
        plan_name = body['PlanName']
        if not validate_unique_rp_name(plan_name):
            return response(409, {  # Conflict
                'error': 'RP_NAME_EXISTS',
                'message': f'A Recovery Plan named "{plan_name}" already exists',
                'existingName': plan_name
            })
        
        # Generate UUID for PlanId
        plan_id = str(uuid.uuid4())
        
        # Create Recovery Plan item
        timestamp = int(time.time())
        item = {
            'PlanId': plan_id,
            'PlanName': body['PlanName'],
            'Description': body.get('Description', ''),  # Optional
            'Waves': body.get('Waves', []),
            'CreatedDate': timestamp,
            'LastModifiedDate': timestamp
        }
        
        # Validate waves if provided
        if item['Waves']:
            validation_error = validate_waves(item['Waves'])
            if validation_error:
                return response(400, {'error': validation_error})
        
        # Store in DynamoDB
        recovery_plans_table.put_item(Item=item)
        
        print(f"Created Recovery Plan: {plan_id}")
        return response(201, item)
        
    except Exception as e:
        print(f"Error creating Recovery Plan: {str(e)}")
        return response(500, {'error': str(e)})


def get_recovery_plans() -> Dict:
    """List all Recovery Plans with latest execution history and conflict info"""
    try:
        result = recovery_plans_table.scan()
        plans = result.get('Items', [])
        
        # Get conflict info for all plans (for graying out Drill/Recovery buttons)
        plans_with_conflicts = get_plans_with_conflicts()

        # Enrich each plan with latest execution data and conflict info
        for plan in plans:
            plan_id = plan.get('PlanId')
            
            # Add conflict info if this plan has conflicts with other active executions
            if plan_id in plans_with_conflicts:
                conflict_info = plans_with_conflicts[plan_id]
                plan['HasServerConflict'] = True
                plan['ConflictInfo'] = conflict_info
            else:
                plan['HasServerConflict'] = False
                plan['ConflictInfo'] = None
            
            # Query ExecutionHistoryTable for latest execution
            try:
                execution_result = execution_history_table.query(
                    IndexName='PlanIdIndex',
                    KeyConditionExpression=Key('PlanId').eq(plan_id),
                    ScanIndexForward=False,  # Sort by StartTime DESC
                    Limit=1  # Get only the latest execution
                )
                
                if execution_result.get('Items'):
                    latest_execution = execution_result['Items'][0]
                    plan['LastExecutionStatus'] = latest_execution.get('Status')
                    plan['LastStartTime'] = latest_execution.get('StartTime')
                    plan['LastEndTime'] = latest_execution.get('EndTime')
                else:
                    # No executions found for this plan
                    plan['LastExecutionStatus'] = None
                    plan['LastStartTime'] = None
                    plan['LastEndTime'] = None
                    
            except Exception as e:
                print(f"Error querying execution history for plan {plan_id}: {str(e)}")
                # Set null values on error
                plan['LastExecutionStatus'] = None
                plan['LastStartTime'] = None
                plan['LastEndTime'] = None

            # Add wave count before transformation
            plan['WaveCount'] = len(plan.get('Waves', []))

        # Transform to camelCase for frontend
        camelcase_plans = []
        for plan in plans:
            camelcase_plans.append(transform_rp_to_camelcase(plan))

        return response(200, {'plans': camelcase_plans, 'count': len(camelcase_plans)})

    except Exception as e:
        print(f"Error listing Recovery Plans: {str(e)}")
        return response(500, {'error': str(e)})


def get_recovery_plan(plan_id: str) -> Dict:
    """Get a single Recovery Plan by ID"""
    try:
        result = recovery_plans_table.get_item(Key={'PlanId': plan_id})

        if 'Item' not in result:
            return response(404, {'error': 'Recovery Plan not found'})

        plan = result['Item']
        plan['WaveCount'] = len(plan.get('Waves', []))
        
        # Transform to camelCase for frontend
        camelcase_plan = transform_rp_to_camelcase(plan)
        
        return response(200, camelcase_plan)

    except Exception as e:
        print(f"Error getting Recovery Plan: {str(e)}")
        return response(500, {'error': str(e)})


def update_recovery_plan(plan_id: str, body: Dict) -> Dict:
    """Update an existing Recovery Plan - blocked if execution in progress"""
    try:
        # Check if plan exists
        result = recovery_plans_table.get_item(Key={'PlanId': plan_id})
        if 'Item' not in result:
            return response(404, {'error': 'Recovery Plan not found'})
        
        existing_plan = result['Item']
        
        # BLOCK: Cannot update plan with active execution
        active_executions = get_active_executions_for_plan(plan_id)
        if active_executions:
            exec_ids = [e.get('ExecutionId') for e in active_executions]
            return response(409, {
                'error': 'PLAN_HAS_ACTIVE_EXECUTION',
                'message': 'Cannot modify Recovery Plan while an execution is in progress',
                'activeExecutions': exec_ids,
                'planId': plan_id
            })
        
        # Validate unique name if changing
        if 'PlanName' in body and body['PlanName'] != existing_plan.get('PlanName'):
            if not validate_unique_rp_name(body['PlanName'], plan_id):
                return response(409, {
                    'error': 'RP_NAME_EXISTS',
                    'message': f'A Recovery Plan named "{body["PlanName"]}" already exists',
                    'existingName': body['PlanName']
                })
        
        # NEW: Pre-write validation for Waves
        if 'Waves' in body:
            print(f"Updating plan {plan_id} with {len(body['Waves'])} waves")
            
            # DEFENSIVE: Validate ServerIds in each wave
            for idx, wave in enumerate(body['Waves']):
                server_ids = wave.get('ServerIds', [])
                if not isinstance(server_ids, list):
                    print(f"ERROR: Wave {idx} ServerIds is not a list: {type(server_ids)}")
                    return response(400, {
                        'error': 'INVALID_WAVE_DATA',
                        'message': f'Wave {idx} has invalid ServerIds format (must be array)',
                        'waveIndex': idx
                    })
                print(f"Wave {idx}: {wave.get('WaveName')} - {len(server_ids)} servers")
            
            validation_error = validate_waves(body['Waves'])
            if validation_error:
                return response(400, {'error': validation_error})
        
        # Build update expression
        update_expression = "SET LastModifiedDate = :timestamp"
        expression_values = {':timestamp': int(time.time())}
        expression_names = {}
        
        updatable_fields = ['PlanName', 'Description', 'RPO', 'RTO', 'Waves']
        for field in updatable_fields:
            if field in body:
                if field == 'Description':
                    update_expression += ", #desc = :desc"
                    expression_values[':desc'] = body['Description']
                    expression_names['#desc'] = 'Description'
                else:
                    update_expression += f", {field} = :{field.lower()}"
                    expression_values[f':{field.lower()}'] = body[field]
        
        # Update item
        update_args = {
            'Key': {'PlanId': plan_id},
            'UpdateExpression': update_expression,
            'ExpressionAttributeValues': expression_values,
            'ReturnValues': 'ALL_NEW'
        }
        
        if expression_names:
            update_args['ExpressionAttributeNames'] = expression_names
        
        result = recovery_plans_table.update_item(**update_args)
        
        print(f"Updated Recovery Plan: {plan_id}")
        return response(200, result['Attributes'])
        
    except Exception as e:
        print(f"Error updating Recovery Plan: {str(e)}")
        return response(500, {'error': str(e)})


def delete_recovery_plan(plan_id: str) -> Dict:
    """Delete a Recovery Plan - blocked if any active execution exists"""
    try:
        # Check for ANY active execution (not just RUNNING)
        active_executions = get_active_executions_for_plan(plan_id)
        
        if active_executions:
            exec_ids = [e.get('ExecutionId') for e in active_executions]
            statuses = [e.get('Status') for e in active_executions]
            print(f"Cannot delete plan {plan_id}: {len(active_executions)} active execution(s)")
            return response(409, {
                'error': 'PLAN_HAS_ACTIVE_EXECUTION',
                'message': f'Cannot delete Recovery Plan while {len(active_executions)} execution(s) are in progress',
                'activeExecutions': exec_ids,
                'activeStatuses': statuses,
                'planId': plan_id
            })
        
        # No active executions, safe to delete
        print(f"Deleting Recovery Plan: {plan_id}")
        recovery_plans_table.delete_item(Key={'PlanId': plan_id})
        
        print(f"Successfully deleted Recovery Plan: {plan_id}")
        return response(200, {
            'message': 'Recovery Plan deleted successfully',
            'planId': plan_id
        })
        
    except Exception as e:
        print(f"Error deleting Recovery Plan {plan_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        return response(500, {
            'error': 'DELETE_FAILED',
            'message': f'Failed to delete Recovery Plan: {str(e)}',
            'planId': plan_id
        })


# ============================================================================
# Execution Handlers
# ============================================================================

def handle_executions(method: str, path_params: Dict, query_params: Dict, body: Dict) -> Dict:
    """Route Execution requests"""
    execution_id = path_params.get('executionId')
    # Use full path for action detection (cancel, pause, resume)
    full_path = path_params.get('_full_path', '')
    
    print(f"EXECUTIONS ROUTE - execution_id: {execution_id}, full_path: {full_path}, method: {method}")
    
    # Handle action-specific routes
    if execution_id and '/cancel' in full_path:
        return cancel_execution(execution_id)
    elif execution_id and '/pause' in full_path:
        return pause_execution(execution_id)
    elif execution_id and '/resume' in full_path:
        return resume_execution(execution_id)
    elif execution_id and '/terminate-instances' in full_path:
        return terminate_recovery_instances(execution_id)
    elif execution_id and '/job-logs' in full_path:
        job_id = query_params.get('jobId')
        return get_job_log_items(execution_id, job_id)
    elif method == 'POST' and not execution_id:
        return execute_recovery_plan(body)
    elif method == 'GET' and execution_id:
        return get_execution_details(execution_id)
    elif method == 'GET':
        # List all executions with optional pagination
        return list_executions(query_params)
    elif method == 'DELETE' and not execution_id:
        # Delete completed executions only (bulk operation)
        return delete_completed_executions()
    else:
        return response(405, {'error': 'Method Not Allowed'})


def execute_recovery_plan(body: Dict, event: Dict = None) -> Dict:
    """Execute a Recovery Plan - Async pattern to avoid API Gateway timeout"""
    try:
        # Extract Cognito user if event provided
        cognito_user = get_cognito_user_from_event(event) if event else {'email': 'system', 'userId': 'system'}
        
        # Validate required fields
        required_fields = ['PlanId', 'ExecutionType', 'InitiatedBy']
        for field in required_fields:
            if field not in body:
                return response(400, {'error': f'Missing required field: {field}'})
        
        plan_id = body['PlanId']
        execution_type = body['ExecutionType']
        
        # Validate execution type
        if execution_type not in ['DRILL', 'RECOVERY']:
            return response(400, {'error': 'Invalid ExecutionType'})
        
        # Get Recovery Plan
        plan_result = recovery_plans_table.get_item(Key={'PlanId': plan_id})
        if 'Item' not in plan_result:
            return response(404, {'error': 'Recovery Plan not found'})
        
        plan = plan_result['Item']
        
        # Validate plan has waves
        if not plan.get('Waves'):
            return response(400, {'error': 'Recovery Plan has no waves configured'})
        
        # BLOCK: Cannot execute plan that already has an active execution
        active_executions = get_active_executions_for_plan(plan_id)
        if active_executions:
            exec_ids = [e.get('ExecutionId') for e in active_executions]
            return response(409, {
                'error': 'PLAN_ALREADY_EXECUTING',
                'message': 'This Recovery Plan already has an execution in progress',
                'activeExecutions': exec_ids,
                'planId': plan_id
            })
        
        # BLOCK: Check for server conflicts with other running executions
        server_conflicts = check_server_conflicts(plan)
        if server_conflicts:
            # Group conflicts by execution
            conflict_executions = {}
            for conflict in server_conflicts:
                exec_id = conflict['conflictingExecutionId']
                if exec_id not in conflict_executions:
                    conflict_executions[exec_id] = {
                        'executionId': exec_id,
                        'planId': conflict['conflictingPlanId'],
                        'servers': []
                    }
                conflict_executions[exec_id]['servers'].append(conflict['serverId'])
            
            return response(409, {
                'error': 'SERVER_CONFLICT',
                'message': f'{len(server_conflicts)} server(s) are already in active executions',
                'conflicts': server_conflicts,
                'conflictingExecutions': list(conflict_executions.values())
            })
        
        # Generate execution ID
        execution_id = str(uuid.uuid4())
        timestamp = int(time.time())
        
        print(f"Creating async execution {execution_id} for plan {plan_id}")
        
        # Create initial execution history record with PENDING status
        history_item = {
            'ExecutionId': execution_id,
            'PlanId': plan_id,
            'ExecutionType': execution_type,
            'Status': 'PENDING',
            'StartTime': timestamp,
            'InitiatedBy': body['InitiatedBy'],
            'Waves': [],
            'TotalWaves': len(plan.get('Waves', []))  # Store total wave count for UI display
        }
        
        # Store execution history immediately
        execution_history_table.put_item(Item=history_item)
        
        # Invoke this same Lambda asynchronously to do the actual work
        # AWS_LAMBDA_FUNCTION_NAME is automatically set by Lambda runtime
        current_function_name = os.environ['AWS_LAMBDA_FUNCTION_NAME']
        
        # Prepare payload for async worker
        worker_payload = {
            'worker': True,  # Flag to route to worker handler
            'executionId': execution_id,
            'planId': plan_id,
            'executionType': execution_type,
            'isDrill': execution_type == 'DRILL',
            'plan': plan,
            'cognitoUser': cognito_user  # Pass Cognito user info to worker
        }
        
        # Invoke async (Event invocation type = fire and forget)
        try:
            invoke_response = lambda_client.invoke(
                FunctionName=current_function_name,
                InvocationType='Event',  # Async invocation
                Payload=json.dumps(worker_payload, cls=DecimalEncoder)
            )
            # Check for invocation errors (StatusCode should be 202 for async)
            status_code = invoke_response.get('StatusCode', 0)
            if status_code != 202:
                raise Exception(f"Async invocation returned unexpected status: {status_code}")
            print(f"Async worker invoked for execution {execution_id}, StatusCode: {status_code}")
        except Exception as invoke_error:
            # If async invocation fails, mark execution as FAILED immediately
            print(f"ERROR: Failed to invoke async worker: {str(invoke_error)}")
            execution_history_table.update_item(
                Key={'ExecutionId': execution_id, 'PlanId': plan_id},
                UpdateExpression='SET #status = :status, EndTime = :end_time, ErrorMessage = :error',
                ExpressionAttributeNames={'#status': 'Status'},
                ExpressionAttributeValues={
                    ':status': 'FAILED',
                    ':end_time': timestamp,
                    ':error': f'Failed to start worker: {str(invoke_error)}'
                }
            )
            return response(500, {
                'error': f'Failed to start execution worker: {str(invoke_error)}',
                'executionId': execution_id
            })
        
        # Return immediately with 202 Accepted
        return response(202, {
            'executionId': execution_id,
            'status': 'PENDING',
            'message': 'Execution started - check status with GET /executions/{id}',
            'statusUrl': f'/executions/{execution_id}'
        })
        
    except Exception as e:
        print(f"Error starting execution: {str(e)}")
        import traceback
        traceback.print_exc()
        return response(500, {'error': str(e)})


def execute_with_step_functions(execution_id: str, plan_id: str, plan: Dict, is_drill: bool, state_machine_arn: str, resume_from_wave: int = None) -> None:
    """
    Execute recovery plan using Step Functions
    This properly waits for EC2 instances to launch by checking participatingServers[].launchStatus
    
    Args:
        resume_from_wave: If set, this is a resumed execution starting from this wave index
    """
    try:
        if resume_from_wave is not None:
            print(f"RESUMING Step Functions execution for {execution_id} from wave {resume_from_wave}")
        else:
            print(f"Starting NEW Step Functions execution for {execution_id}")
        
        # Prepare Step Functions input
        # Step Functions input format for step-functions-stack.yaml state machine
        # Uses 'Plan' (singular) not 'Plans' (array)
        # ALWAYS include ResumeFromWave (null for new executions) so Step Functions doesn't fail
        sfn_input = {
            'Execution': {'Id': execution_id},
            'Plan': {
                'PlanId': plan_id,
                'PlanName': plan.get('PlanName', 'Unknown'),
                'Waves': plan.get('Waves', [])
            },
            'IsDrill': is_drill,
            'ResumeFromWave': resume_from_wave  # None for new executions, wave index for resume
        }
        
        # For resumed executions, use a unique name suffix to avoid conflicts
        sfn_name = execution_id if resume_from_wave is None else f"{execution_id}-resume-{resume_from_wave}"
        
        # Start Step Functions execution
        sfn_response = stepfunctions.start_execution(
            stateMachineArn=state_machine_arn,
            name=sfn_name,
            input=json.dumps(sfn_input, cls=DecimalEncoder)
        )
        
        print(f"Step Functions execution started: {sfn_response['executionArn']}")
        
        # Update DynamoDB with Step Functions execution ARN
        execution_history_table.update_item(
            Key={'ExecutionId': execution_id, 'PlanId': plan_id},
            UpdateExpression='SET StateMachineArn = :arn, #status = :status',
            ExpressionAttributeNames={'#status': 'Status'},
            ExpressionAttributeValues={
                ':arn': sfn_response['executionArn'],
                ':status': 'RUNNING'
            }
        )
        
        print(f"✅ Step Functions execution initiated successfully")
        
    except Exception as e:
        print(f"❌ Error starting Step Functions execution: {e}")
        import traceback
        traceback.print_exc()
        
        # Update execution as failed
        try:
            execution_history_table.update_item(
                Key={'ExecutionId': execution_id, 'PlanId': plan_id},
                UpdateExpression='SET #status = :status, ErrorMessage = :error',
                ExpressionAttributeNames={'#status': 'Status'},
                ExpressionAttributeValues={
                    ':status': 'FAILED',
                    ':error': str(e)
                }
            )
        except Exception as update_error:
            print(f"Error updating execution failure: {update_error}")


def execute_recovery_plan_worker(payload: Dict) -> None:
    """Background worker - executes recovery via Step Functions
    
    Handles both new executions and resumed executions.
    For resumed executions, resumeFromWave specifies which wave to start from.
    """
    try:
        execution_id = payload['executionId']
        plan_id = payload['planId']
        is_drill = payload['isDrill']
        plan = payload['plan']
        cognito_user = payload.get('cognitoUser', {'email': 'system', 'userId': 'system'})
        resume_from_wave = payload.get('resumeFromWave')  # None for new executions, wave index for resume
        
        if resume_from_wave is not None:
            print(f"Worker RESUMING execution {execution_id} from wave {resume_from_wave} (isDrill: {is_drill})")
        else:
            print(f"Worker initiating NEW execution {execution_id} (isDrill: {is_drill})")
        print(f"Initiated by: {cognito_user.get('email')}")
        
        # Always use Step Functions
        state_machine_arn = os.environ.get('STATE_MACHINE_ARN')
        if not state_machine_arn:
            raise ValueError("STATE_MACHINE_ARN environment variable not set")
        
        print(f"Using Step Functions for execution {execution_id}")
        return execute_with_step_functions(execution_id, plan_id, plan, is_drill, state_machine_arn, resume_from_wave)
        
    except Exception as e:
        print(f"Worker error for execution {execution_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Mark execution as failed
        try:
            execution_history_table.update_item(
                Key={'ExecutionId': execution_id, 'PlanId': plan_id},
                UpdateExpression='SET #status = :status, EndTime = :endtime, ErrorMessage = :error',
                ExpressionAttributeNames={'#status': 'Status'},
                ExpressionAttributeValues={
                    ':status': 'FAILED',
                    ':endtime': int(time.time()),
                    ':error': str(e)
                }
            )
        except Exception as update_error:
            print(f"Failed to update error status: {str(update_error)}")


def initiate_wave(
    wave: Dict, 
    protection_group_id: str, 
    execution_id: str, 
    is_drill: bool, 
    execution_type: str = 'DRILL',
    plan_name: str = None,  # STEP 6: Add metadata parameters
    wave_name: str = None,
    wave_number: int = None,
    cognito_user: Dict = None
) -> Dict:
    """Initiate DRS recovery jobs for a wave without waiting for completion"""
    try:
        # Get Protection Group
        pg_result = protection_groups_table.get_item(Key={'GroupId': protection_group_id})
        if 'Item' not in pg_result:
            return {
                'WaveName': wave.get('name', 'Unknown'),
                'ProtectionGroupId': protection_group_id,
                'Status': 'FAILED',
                'Error': 'Protection Group not found',
                'Servers': [],
                'StartTime': int(time.time())
            }
        
        pg = pg_result['Item']
        region = pg['Region']
        
        # Get servers from both wave and protection group
        pg_servers = pg.get('SourceServerIds', [])
        wave_servers = wave.get('ServerIds', [])
        
        # Filter to only launch servers specified in this wave
        # This ensures each wave launches its designated subset of servers
        if wave_servers:
            # Wave has explicit server list - filter PG servers to this subset
            server_ids = [s for s in wave_servers if s in pg_servers]
            print(f"Wave specifies {len(wave_servers)} servers, {len(server_ids)} are in Protection Group")
        else:
            # No ServerIds in wave - launch all PG servers (legacy behavior)
            server_ids = pg_servers
            print(f"Wave has no ServerIds field, launching all {len(server_ids)} Protection Group servers")
        
        if not server_ids:
            return {
                'WaveName': wave.get('name', 'Unknown'),
                'ProtectionGroupId': protection_group_id,
                'Status': 'INITIATED',
                'Servers': [],
                'StartTime': int(time.time())
            }
        
        print(f"Initiating recovery for {len(server_ids)} servers in region {region}")
        
        # CRITICAL FIX: Launch ALL servers in wave with ONE DRS API call
        # This gives us ONE job ID per wave (which poller expects)
        # STEP 6: Pass metadata to start_drs_recovery_for_wave
        wave_job_result = start_drs_recovery_for_wave(
            server_ids, region, is_drill, execution_id, execution_type,
            plan_name=plan_name,
            wave_name=wave_name,
            wave_number=wave_number,
            cognito_user=cognito_user
        )
        
        # Extract job ID and server results
        wave_job_id = wave_job_result.get('JobId')
        server_results = wave_job_result.get('Servers', [])
        
        # Wave status is INITIATED (not IN_PROGRESS)
        # External poller will update to IN_PROGRESS/COMPLETED
        has_failures = any(s['Status'] == 'FAILED' for s in server_results)
        wave_status = 'PARTIAL' if has_failures else 'INITIATED'
        
        return {
            'WaveName': wave.get('name', 'Unknown'),
            'WaveId': wave.get('WaveId') or wave.get('waveNumber'),  # Support both formats
            'JobId': wave_job_id,  # CRITICAL: Wave-level Job ID for poller
            'ProtectionGroupId': protection_group_id,
            'Region': region,
            'Status': wave_status,
            'Servers': server_results,
            'StartTime': int(time.time())
        }
        
    except Exception as e:
        print(f"Error initiating wave: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'WaveName': wave.get('name', 'Unknown'),
            'ProtectionGroupId': protection_group_id,
            'Status': 'FAILED',
            'Error': str(e),
            'Servers': [],
            'StartTime': int(time.time())
        }


def get_server_launch_configurations(region: str, server_ids: List[str]) -> Dict[str, Dict]:
    """
    Fetch launch configurations for all servers in wave from DRS
    
    Args:
        region: AWS region
        server_ids: List of DRS source server IDs
    
    Returns:
        Dictionary mapping server_id to launch configuration
        
    Example:
        {
            's-111': {
                'targetInstanceTypeRightSizingMethod': 'BASIC',
                'copyPrivateIp': False,
                'copyTags': True
            },
            's-222': {
                'targetInstanceTypeRightSizingMethod': 'NONE',
                'copyPrivateIp': True,
                'copyTags': True
            }
        }
    """
    drs_client = boto3.client('drs', region_name=region)
    configs = {}
    
    for server_id in server_ids:
        try:
            response = drs_client.get_launch_configuration(
                sourceServerID=server_id
            )
            
            configs[server_id] = {
                'targetInstanceTypeRightSizingMethod': response.get('targetInstanceTypeRightSizingMethod', 'BASIC'),
                'copyPrivateIp': response.get('copyPrivateIp', False),
                'copyTags': response.get('copyTags', True),
                'launchDisposition': response.get('launchDisposition', 'STARTED'),
                'bootMode': response.get('bootMode', 'USE_DEFAULT')
            }
            
            print(f"[Launch Config] {server_id}: rightSizing={configs[server_id]['targetInstanceTypeRightSizingMethod']}")
            
        except Exception as e:
            print(f"[Launch Config] ERROR for {server_id}: {str(e)}")
            # FALLBACK: Use safe defaults if config query fails
            configs[server_id] = {
                'targetInstanceTypeRightSizingMethod': 'BASIC',
                'copyPrivateIp': False,
                'copyTags': True,
                'launchDisposition': 'STARTED',
                'bootMode': 'USE_DEFAULT'
            }
            print(f"[Launch Config] {server_id}: Using fallback defaults")
    
    return configs


def start_drs_recovery_for_wave(
    server_ids: List[str], 
    region: str, 
    is_drill: bool, 
    execution_id: str, 
    execution_type: str = 'DRILL',
    plan_name: str = None,  # STEP 7: Add metadata parameters
    wave_name: str = None,
    wave_number: int = None,
    cognito_user: Dict = None
) -> Dict:
    """
    Launch DRS recovery for all servers in a wave with ONE API call
    
    CRITICAL PATTERN (from DRS drill learning session):
    - Launches ALL servers in wave with SINGLE start_recovery() call
    - Returns ONE job ID for entire wave (not per server)
    - This job ID is what ExecutionPoller tracks for wave completion
    - All servers in wave share same job ID and are tracked together
    
    DRS API Response Structure:
    {
        'job': {
            'jobID': 'drsjob-xxxxx',
            'status': 'PENDING',  # Initial status
            'type': 'LAUNCH',
            'participatingServers': [
                {'sourceServerID': 's-xxx', 'launchStatus': 'PENDING'}
            ]
        }
    }
    
    Expected Job Status Progression:
    PENDING → STARTED → COMPLETED (or FAILED)
    
    Per-Server Launch Status:
    PENDING → LAUNCHED → (job completes)
    
    Args:
        server_ids: List of DRS source server IDs to launch
        region: AWS region for DRS API call
        is_drill: True for drill, False for actual recovery
        execution_id: Execution ID for tracking
        execution_type: 'DRILL' or 'RECOVERY'
    
    Returns:
        Dict with JobId (wave-level) and Servers array
    """
    try:
        drs_client = boto3.client('drs', region_name=region)
        
        print(f"[DRS API] Starting {execution_type} {'drill' if is_drill else 'recovery'}")
        print(f"[DRS API] Region: {region}, Servers: {len(server_ids)}")
        print(f"[DRS API] Server IDs: {server_ids}")
        
        # STEP 1: Fetch per-server launch configurations from DRS
        print(f"[DRS API] Fetching launch configurations for {len(server_ids)} servers...")
        launch_configs = get_server_launch_configurations(region, server_ids)

        # STEP 3: Build sourceServers array (simplified - DRS uses latest snapshot automatically)
        source_servers = [{'sourceServerID': sid} for sid in server_ids]
        print(f"[DRS API] Built sourceServers array for {len(server_ids)} servers")

        # CRITICAL FIX: Do NOT pass tags to start_recovery()
        # The reference implementation (drs-plan-automation) does NOT use tags
        # CLI without tags works, code with tags fails (conversion skipped)
        # Tags were causing DRS to skip the CONVERSION phase entirely
        
        # STEP 4: Start recovery for ALL servers in ONE API call WITHOUT TAGS
        print(f"[DRS API] Calling start_recovery() WITHOUT tags (reference implementation pattern)")
        print(f"[DRS API]   sourceServers: {len(source_servers)} servers")
        print(f"[DRS API]   isDrill: {is_drill}")
        print(f"[DRS API]   NOTE: Tags removed - they were causing conversion to be skipped!")
        
        response = drs_client.start_recovery(
            sourceServers=source_servers,
            isDrill=is_drill
            # NO TAGS - this is the fix!
        )
        
        # Validate response structure (defensive programming)
        if 'job' not in response:
            raise Exception("DRS API response missing 'job' field")
        
        job = response['job']
        job_id = job.get('jobID')
        
        if not job_id:
            raise Exception("DRS API response missing 'jobID' field")
        
        job_status = job.get('status', 'UNKNOWN')
        job_type = job.get('type', 'UNKNOWN')
        
        print(f"[DRS API] ✅ Job created successfully")
        print(f"[DRS API]   Job ID: {job_id}")
        print(f"[DRS API]   Status: {job_status}")
        print(f"[DRS API]   Type: {job_type}")
        print(f"[DRS API]   Servers: {len(server_ids)} (all share this job ID)")
        
        # Build server results array (all servers share same job ID)
        server_results = []
        for server_id in server_ids:
            server_results.append({
                'SourceServerId': server_id,
                'RecoveryJobId': job_id,  # Same job ID for all servers
                'Status': 'LAUNCHING',
                'InstanceId': None,
                'LaunchTime': int(time.time()),
                'Error': None
            })
        
        print(f"[DRS API] Wave initiation complete - ExecutionPoller will track job {job_id}")
        
        return {
            'JobId': job_id,  # Wave-level Job ID for poller
            'Servers': server_results
        }
        
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        
        print(f"[DRS API] ❌ Failed to start recovery for wave")
        print(f"[DRS API]   Error Type: {error_type}")
        print(f"[DRS API]   Error Message: {error_msg}")
        print(f"[DRS API]   Region: {region}")
        print(f"[DRS API]   Server Count: {len(server_ids)}")
        
        # Log full traceback for debugging
        import traceback
        traceback.print_exc()
        
        # Return failed results for all servers
        server_results = []
        for server_id in server_ids:
            server_results.append({
                'SourceServerId': server_id,
                'Status': 'FAILED',
                'Error': f"{error_type}: {error_msg}",
                'LaunchTime': int(time.time())
            })
        
        return {
            'JobId': None,
            'Servers': server_results
        }


def start_drs_recovery(server_id: str, region: str, is_drill: bool, execution_id: str, execution_type: str = 'DRILL') -> Dict:
    """Launch DRS recovery for a single source server"""
    try:
        drs_client = boto3.client('drs', region_name=region)
        
        print(f"Starting {execution_type} {'drill' if is_drill else 'recovery'} for server {server_id}")
        
        # Start recovery job
        # Omit recoverySnapshotID to use latest point-in-time snapshot (AWS default)
        response = drs_client.start_recovery(
            sourceServers=[{
                'sourceServerID': server_id
            }],
            isDrill=is_drill
        )
        
        job = response.get('job', {})
        job_id = job.get('jobID', 'unknown')
        
        print(f"Started recovery job {job_id} for server {server_id}")
        
        return {
            'SourceServerId': server_id,
            'RecoveryJobId': job_id,
            'Status': 'LAUNCHING',
            'InstanceId': None,  # Will be populated later when instance launches
            'LaunchTime': int(time.time()),
            'Error': None
        }
        
    except Exception as e:
        error_msg = str(e)
        print(f"Failed to start recovery for server {server_id}: {error_msg}")
        return {
            'SourceServerId': server_id,
            'Status': 'FAILED',
            'Error': error_msg,
            'LaunchTime': int(time.time())
        }


def start_drs_recovery_with_retry(server_id: str, region: str, is_drill: bool, execution_id: str) -> Dict:
    """Launch DRS recovery with ConflictException retry logic"""
    from botocore.exceptions import ClientError
    
    max_retries = 3
    base_delay = 30  # Base delay in seconds
    
    for attempt in range(max_retries):
        try:
            return start_drs_recovery(server_id, region, is_drill, execution_id)
        except ClientError as e:
            error_code = e.response['Error']['Code']
            
            # Only retry on ConflictException
            if error_code == 'ConflictException' and attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)  # Exponential backoff: 30s, 60s, 120s
                print(f"ConflictException for server {server_id} (attempt {attempt + 1}/{max_retries})")
                print(f"Server is being processed by another job, retrying in {delay}s...")
                time.sleep(delay)
                continue
            
            # Re-raise if not ConflictException or last attempt
            raise
        except Exception as e:
            # Re-raise non-ClientError exceptions immediately
            raise


def get_execution_status(execution_id: str) -> Dict:
    """Get current execution status"""
    try:
        # Get from DynamoDB using Query (table has composite key: ExecutionId + PlanId)
        result = execution_history_table.query(
            KeyConditionExpression=Key('ExecutionId').eq(execution_id),
            Limit=1
        )
        
        if not result.get('Items'):
            return response(404, {'error': 'Execution not found'})
        
        execution = result['Items'][0]
        
        # Get current status from Step Functions if still running
        if execution['Status'] == 'RUNNING':
            try:
                # Build proper Step Functions execution ARN from execution ID
                state_machine_arn = execution.get('StateMachineArn')
                if state_machine_arn:
                    sf_response = stepfunctions.describe_execution(
                        executionArn=state_machine_arn
                    )
                    execution['StepFunctionsStatus'] = sf_response['status']
            except Exception as e:
                print(f"Error getting Step Functions status: {str(e)}")
        
        return response(200, execution)
        
    except Exception as e:
        print(f"Error getting execution status: {str(e)}")
        return response(500, {'error': str(e)})


def get_execution_history(plan_id: str) -> Dict:
    """Get execution history for a Recovery Plan"""
    try:
        result = execution_history_table.query(
            IndexName='PlanIdIndex',
            KeyConditionExpression=Key('PlanId').eq(plan_id),
            ScanIndexForward=False  # Sort by StartTime descending
        )
        
        executions = result.get('Items', [])
        
        return response(200, {
            'executions': executions,
            'count': len(executions)
        })
        
    except Exception as e:
        print(f"Error getting execution history: {str(e)}")
        return response(500, {'error': str(e)})


def list_executions(query_params: Dict) -> Dict:
    """List all executions with optional pagination"""
    try:
        limit = int(query_params.get('limit', 50))
        next_token = query_params.get('nextToken')
        
        # Scan execution history table
        scan_args = {
            'Limit': min(limit, 100)  # Cap at 100
        }
        
        if next_token:
            scan_args['ExclusiveStartKey'] = json.loads(next_token)
        
        result = execution_history_table.scan(**scan_args)
        
        executions = result.get('Items', [])
        
        # Sort by StartTime descending (most recent first)
        executions.sort(key=lambda x: x.get('StartTime', 0), reverse=True)
        
        # Enrich with recovery plan names and transform to camelCase
        transformed_executions = []
        for execution in executions:
            try:
                plan_id = execution.get('PlanId')
                if plan_id:
                    plan_result = recovery_plans_table.get_item(Key={'PlanId': plan_id})
                    if 'Item' in plan_result:
                        execution['RecoveryPlanName'] = plan_result['Item'].get('PlanName', 'Unknown')
                    else:
                        execution['RecoveryPlanName'] = 'Unknown'
            except Exception as e:
                print(f"Error enriching execution {execution.get('ExecutionId')}: {str(e)}")
                execution['RecoveryPlanName'] = 'Unknown'
            
            # Transform to camelCase for frontend
            transformed_executions.append(transform_execution_to_camelcase(execution))
        
        # Build response with pagination
        response_data = {
            'items': transformed_executions,
            'count': len(transformed_executions)
        }
        
        if 'LastEvaluatedKey' in result:
            response_data['nextToken'] = json.dumps(result['LastEvaluatedKey'])
        else:
            response_data['nextToken'] = None
        
        print(f"Listed {len(executions)} executions")
        return response(200, response_data)
        
    except Exception as e:
        print(f"Error listing executions: {str(e)}")
        import traceback
        traceback.print_exc()
        return response(500, {'error': str(e)})


def get_server_details_map(server_ids: List[str], region: str = 'us-east-1') -> Dict[str, Dict]:
    """
    Get DRS source server details for a list of server IDs.
    Returns a map of serverId -> {hostname, name, region, sourceInstanceId, sourceAccountId, ...}
    """
    server_map = {}
    if not server_ids:
        return server_map
    
    try:
        # Use regional DRS client if needed
        drs_client = boto3.client('drs', region_name=region)
        
        # Get source servers (DRS API doesn't support filtering by ID list, so get all and filter)
        paginator = drs_client.get_paginator('describe_source_servers')
        for page in paginator.paginate():
            for server in page.get('items', []):
                source_id = server.get('sourceServerID')
                if source_id in server_ids:
                    # Extract hostname and source instance ID from sourceProperties
                    source_props = server.get('sourceProperties', {})
                    hostname = source_props.get('identificationHints', {}).get('hostname', '')
                    
                    # Get source EC2 instance ID (the original instance being replicated)
                    source_instance_id = source_props.get('identificationHints', {}).get('awsInstanceID', '')
                    
                    # Get Name tag if available
                    tags = server.get('tags', {})
                    name_tag = tags.get('Name', '')
                    
                    # Get source account ID from staging area info or ARN
                    source_account_id = ''
                    staging_area = server.get('stagingArea', {})
                    if staging_area:
                        source_account_id = staging_area.get('stagingAccountID', '')
                    # Fallback: extract from ARN if available
                    if not source_account_id:
                        arn = server.get('arn', '')
                        if arn:
                            # ARN format: arn:aws:drs:region:account:source-server/id
                            arn_parts = arn.split(':')
                            if len(arn_parts) >= 5:
                                source_account_id = arn_parts[4]
                    
                    # Extract source IP from network interfaces
                    network_interfaces = source_props.get('networkInterfaces', [])
                    source_ip = ''
                    if network_interfaces:
                        # Get first private IP from first interface
                        first_iface = network_interfaces[0]
                        ips = first_iface.get('ips', [])
                        if ips:
                            source_ip = ips[0]
                    
                    # Extract source region from replication info
                    source_region = ''
                    data_rep_info = server.get('dataReplicationInfo', {})
                    replicated_disks = data_rep_info.get('replicatedDisks', [])
                    if replicated_disks:
                        # Extract region from device name or use staging area region
                        staging_area = server.get('stagingArea', {})
                        source_region = staging_area.get('stagingSourceServerArn', '').split(':')[3] if staging_area.get('stagingSourceServerArn') else ''
                    
                    # Fallback: get source region from sourceProperties
                    if not source_region:
                        source_region = source_props.get('identificationHints', {}).get('awsInstanceID', '').split(':')[3] if ':' in source_props.get('identificationHints', {}).get('awsInstanceID', '') else ''
                    
                    server_map[source_id] = {
                        'hostname': hostname,
                        'nameTag': name_tag,  # Will be updated from EC2 below
                        'region': region,
                        'sourceInstanceId': source_instance_id,
                        'sourceAccountId': source_account_id,
                        'sourceIp': source_ip,
                        'sourceRegion': source_region or region,  # Fallback to target region if not found
                        'replicationState': server.get('dataReplicationInfo', {}).get('dataReplicationState', 'UNKNOWN'),
                        'lastLaunchResult': server.get('lastLaunchResult', 'NOT_STARTED'),
                    }
        
        # Fetch EC2 Name tags from source instances
        source_instance_ids = [s['sourceInstanceId'] for s in server_map.values() if s.get('sourceInstanceId')]
        if source_instance_ids:
            try:
                ec2_client = boto3.client('ec2', region_name=region)
                ec2_response = ec2_client.describe_instances(InstanceIds=source_instance_ids)
                ec2_name_tags = {}
                for reservation in ec2_response.get('Reservations', []):
                    for instance in reservation.get('Instances', []):
                        instance_id = instance.get('InstanceId', '')
                        for tag in instance.get('Tags', []):
                            if tag.get('Key') == 'Name':
                                ec2_name_tags[instance_id] = tag.get('Value', '')
                                break
                
                # Update server_map with EC2 Name tags
                for source_id, details in server_map.items():
                    instance_id = details.get('sourceInstanceId')
                    if instance_id and instance_id in ec2_name_tags:
                        details['nameTag'] = ec2_name_tags[instance_id]
            except Exception as ec2_error:
                print(f"Error fetching EC2 Name tags: {ec2_error}")
                
    except Exception as e:
        print(f"Error getting server details: {e}")
    
    return server_map


def enrich_execution_with_server_details(execution: Dict) -> Dict:
    """
    Enrich execution waves with server details (hostname, name tag, region).
    """
    waves = execution.get('Waves', [])
    if not waves:
        return execution
    
    # Collect all server IDs and regions from waves
    all_server_ids = set()
    regions = set()
    for wave in waves:
        server_ids = wave.get('ServerIds', [])
        all_server_ids.update(server_ids)
        region = wave.get('Region', 'us-east-1')
        regions.add(region)
    
    if not all_server_ids:
        return execution
    
    # Get server details for each region
    server_details_map = {}
    for region in regions:
        region_servers = get_server_details_map(list(all_server_ids), region)
        server_details_map.update(region_servers)
    
    # Enrich waves with server details
    for wave in waves:
        server_ids = wave.get('ServerIds', [])
        region = wave.get('Region', 'us-east-1')
        
        # Build enriched server list
        enriched_servers = []
        for server_id in server_ids:
            details = server_details_map.get(server_id, {})
            enriched_servers.append({
                'SourceServerId': server_id,
                'Hostname': details.get('hostname', ''),
                'NameTag': details.get('nameTag', ''),
                'Region': region,
                'SourceInstanceId': details.get('sourceInstanceId', ''),
                'SourceAccountId': details.get('sourceAccountId', ''),
                'SourceIp': details.get('sourceIp', ''),
                'SourceRegion': details.get('sourceRegion', ''),
                'ReplicationState': details.get('replicationState', 'UNKNOWN'),
            })
        
        # Add enriched servers to wave
        wave['EnrichedServers'] = enriched_servers
    
    return execution


def get_execution_details(execution_id: str) -> Dict:
    """Get detailed information about a specific execution"""
    try:
        # Handle both UUID and ARN formats for backwards compatibility
        # ARN format: arn:aws:states:region:account:execution:state-machine-name:execution-uuid
        # Extract UUID from ARN if provided
        if execution_id.startswith('arn:'):
            # Extract the last segment which is the UUID
            execution_id = execution_id.split(':')[-1]
            print(f"Extracted UUID from ARN: {execution_id}")
        
        # Get from DynamoDB using query (table has composite key: ExecutionId + PlanId)
        result = execution_history_table.query(
            KeyConditionExpression=Key('ExecutionId').eq(execution_id),
            Limit=1
        )

        if 'Items' not in result or len(result['Items']) == 0:
            return response(404, {'error': 'Execution not found'})

        execution = result['Items'][0]
        
        # Enrich with recovery plan details
        try:
            plan_id = execution.get('PlanId')
            if plan_id:
                plan_result = recovery_plans_table.get_item(Key={'PlanId': plan_id})
                if 'Item' in plan_result:
                    plan = plan_result['Item']
                    execution['RecoveryPlanName'] = plan.get('PlanName', 'Unknown')
                    execution['RecoveryPlanDescription'] = plan.get('Description', '')
                    execution['TotalWaves'] = len(plan.get('Waves', []))
        except Exception as e:
            print(f"Error enriching execution with plan details: {str(e)}")
        
        # Enrich with server details (hostname, name tag, region)
        try:
            execution = enrich_execution_with_server_details(execution)
        except Exception as e:
            print(f"Error enriching execution with server details: {str(e)}")
        
        # Get current status from Step Functions if still running and has StateMachineArn
        if execution.get('Status') == 'RUNNING' and execution.get('StateMachineArn'):
            try:
                sf_response = stepfunctions.describe_execution(
                    executionArn=execution.get('StateMachineArn')
                )
                execution['StepFunctionsStatus'] = sf_response['status']
                
                # Update DynamoDB if Step Functions shows completion
                if sf_response['status'] in ['SUCCEEDED', 'FAILED', 'TIMED_OUT', 'ABORTED']:
                    new_status = 'COMPLETED' if sf_response['status'] == 'SUCCEEDED' else 'FAILED'
                    execution_history_table.update_item(
                        Key={'ExecutionId': execution_id, 'PlanId': execution.get('PlanId')},
                        UpdateExpression='SET #status = :status, EndTime = :endtime',
                        ExpressionAttributeNames={'#status': 'Status'},
                        ExpressionAttributeValues={
                            ':status': new_status,
                            ':endtime': int(time.time())
                        }
                    )
                    execution['Status'] = new_status
                    execution['EndTime'] = int(time.time())
            except Exception as e:
                print(f"Error getting Step Functions status: {str(e)}")
        
        # CONSISTENCY FIX: Transform to camelCase for frontend (same as list_executions)
        # This ensures ALL API endpoints return consistent camelCase format
        transformed_execution = transform_execution_to_camelcase(execution)
        return response(200, transformed_execution)
        
    except Exception as e:
        print(f"Error getting execution details: {str(e)}")
        return response(500, {'error': str(e)})


def cancel_execution(execution_id: str) -> Dict:
    """Cancel a running execution - cancels only pending waves, not completed or in-progress ones.
    
    Behavior:
    - COMPLETED waves: Preserved as-is
    - IN_PROGRESS/POLLING/LAUNCHING waves: Continue running (not interrupted)
    - PENDING/NOT_STARTED waves: Marked as CANCELLED
    - Waves not yet started (from plan): Added with CANCELLED status
    - Overall execution status: Set to CANCELLED only if no waves are still running
    """
    try:
        # FIX: Query by ExecutionId to get PlanId (composite key required)
        result = execution_history_table.query(
            KeyConditionExpression=Key('ExecutionId').eq(execution_id),
            Limit=1
        )
        
        if not result.get('Items'):
            return response(404, {'error': 'Execution not found'})
        
        execution = result['Items'][0]
        plan_id = execution.get('PlanId')
        
        # Check if execution is still running
        current_status = execution.get('Status')
        if current_status not in ['RUNNING', 'PAUSED', 'PAUSE_PENDING', 'CANCELLING', 'IN_PROGRESS', 'POLLING', 'INITIATED']:
            return response(400, {
                'error': 'Execution is not running',
                'currentStatus': current_status
            })
        
        # Get waves from execution and plan
        waves = execution.get('Waves', [])
        timestamp = int(time.time())
        
        # Get recovery plan to find waves that haven't started yet
        plan_waves = []
        try:
            plan_result = recovery_plans_table.get_item(Key={'PlanId': plan_id})
            if 'Item' in plan_result:
                plan_waves = plan_result['Item'].get('Waves', [])
        except Exception as e:
            print(f"Error getting recovery plan: {e}")
        
        # Track wave states
        completed_waves = []
        in_progress_waves = []
        cancelled_waves = []
        
        # Statuses that indicate a wave is done
        completed_statuses = ['COMPLETED', 'FAILED', 'TIMEOUT']
        # Statuses that indicate a wave is currently running
        in_progress_statuses = ['IN_PROGRESS', 'POLLING', 'LAUNCHING', 'INITIATED', 'STARTED']
        
        # Track which wave numbers exist in execution
        existing_wave_numbers = set()
        
        for i, wave in enumerate(waves):
            wave_status = (wave.get('Status') or '').upper()
            wave_number = wave.get('WaveNumber', i)
            existing_wave_numbers.add(wave_number)
            
            if wave_status in completed_statuses:
                completed_waves.append(wave_number)
                # Leave completed waves unchanged
            elif wave_status in in_progress_statuses:
                in_progress_waves.append(wave_number)
                # Leave in-progress waves running - they will complete naturally
            else:
                # Pending/not started waves in execution - mark as CANCELLED
                waves[i]['Status'] = 'CANCELLED'
                waves[i]['EndTime'] = timestamp
                cancelled_waves.append(wave_number)
        
        # Add waves from plan that haven't started yet (not in execution's Waves array)
        for i, plan_wave in enumerate(plan_waves):
            wave_number = plan_wave.get('WaveNumber', i)
            if wave_number not in existing_wave_numbers:
                # This wave hasn't started - add it as CANCELLED
                cancelled_wave = {
                    'WaveNumber': wave_number,
                    'WaveName': plan_wave.get('WaveName', f'Wave {wave_number + 1}'),
                    'Status': 'CANCELLED',
                    'EndTime': timestamp,
                    'ProtectionGroupId': plan_wave.get('ProtectionGroupId'),
                    'ServerIds': plan_wave.get('ServerIds', [])
                }
                waves.append(cancelled_wave)
                cancelled_waves.append(wave_number)
        
        # Sort waves by wave number for consistent display
        waves.sort(key=lambda w: w.get('WaveNumber', 0))
        
        # Stop Step Functions execution only if no waves are in progress
        # If a wave is running, let it complete naturally
        if not in_progress_waves:
            try:
                # amazonq-ignore-next-line
                stepfunctions.stop_execution(
                    executionArn=execution_id,
                    error='UserCancelled',
                    cause='Execution cancelled by user'
                )
                print(f"Stopped Step Functions execution: {execution_id}")
            except Exception as e:
                print(f"Error stopping Step Functions execution: {str(e)}")
                # Continue to update DynamoDB even if Step Functions call fails
        
        # Determine final execution status
        # If waves are still in progress, mark as CANCELLING (will be finalized when wave completes)
        # If no waves in progress, mark as CANCELLED
        final_status = 'CANCELLING' if in_progress_waves else 'CANCELLED'
        
        # Update DynamoDB with updated waves and status
        update_expression = 'SET #status = :status, Waves = :waves'
        expression_values = {
            ':status': final_status,
            ':waves': waves
        }
        
        # Only set EndTime if fully cancelled (no in-progress waves)
        if not in_progress_waves:
            update_expression += ', EndTime = :endtime'
            expression_values[':endtime'] = timestamp
        
        execution_history_table.update_item(
            Key={'ExecutionId': execution_id, 'PlanId': plan_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames={'#status': 'Status'},
            ExpressionAttributeValues=expression_values
        )
        
        print(f"Cancel execution {execution_id}: completed={completed_waves}, in_progress={in_progress_waves}, cancelled={cancelled_waves}")
        
        return response(200, {
            'executionId': execution_id,
            'status': final_status,
            'message': f'Execution {"cancelling" if in_progress_waves else "cancelled"} successfully',
            'details': {
                'completedWaves': completed_waves,
                'inProgressWaves': in_progress_waves,
                'cancelledWaves': cancelled_waves
            }
        })
        
    except Exception as e:
        print(f"Error cancelling execution: {str(e)}")
        return response(500, {'error': str(e)})


def pause_execution(execution_id: str) -> Dict:
    """Pause execution - schedules pause after current wave completes.
    
    Behavior:
    - If wave is in progress AND pending waves exist: Mark as PAUSE_PENDING
      (current wave continues, pause takes effect before next wave)
    - If between waves AND pending waves exist: Mark as PAUSED immediately
    - If no pending waves: Error (nothing to pause)
    - Single wave executions cannot be paused
    """
    try:
        result = execution_history_table.query(
            KeyConditionExpression=Key('ExecutionId').eq(execution_id),
            Limit=1
        )
        
        if not result.get('Items'):
            return response(404, {'error': 'Execution not found'})
        
        execution = result['Items'][0]
        plan_id = execution.get('PlanId')
        current_status = execution.get('Status', '')
        
        # Check if execution is in a pausable state
        if current_status not in ['RUNNING', 'IN_PROGRESS', 'POLLING']:
            return response(400, {
                'error': 'Execution cannot be paused',
                'currentStatus': current_status,
                'reason': 'Execution must be running to pause'
            })
        
        # Check wave states
        waves = execution.get('Waves', [])
        if not waves:
            return response(400, {
                'error': 'No waves found in execution',
                'currentStatus': current_status
            })
        
        # Single wave executions cannot be paused
        if len(waves) == 1:
            return response(400, {
                'error': 'Cannot pause single-wave execution',
                'reason': 'Pause is only available for multi-wave recovery plans',
                'currentStatus': current_status
            })
        
        # Find current wave state
        completed_statuses = ['COMPLETED', 'FAILED', 'TIMEOUT', 'CANCELLED']
        in_progress_statuses = ['IN_PROGRESS', 'POLLING', 'LAUNCHING', 'INITIATED', 'STARTED']
        
        has_in_progress_wave = False
        has_pending_wave = False
        current_wave_number = 0
        
        for i, wave in enumerate(waves):
            wave_status = (wave.get('Status') or '').upper()
            wave_number = wave.get('WaveNumber', i + 1)
            
            if wave_status in in_progress_statuses:
                has_in_progress_wave = True
                current_wave_number = wave_number
            elif wave_status not in completed_statuses and wave_status not in ['CANCELLED']:
                # Pending wave (empty status, PENDING, NOT_STARTED)
                has_pending_wave = True
        
        # Must have pending waves to pause
        if not has_pending_wave:
            return response(400, {
                'error': 'Cannot pause - no pending waves remaining',
                'reason': 'All waves have already completed or failed',
                'currentStatus': current_status
            })
        
        # Determine pause type
        if has_in_progress_wave:
            # Wave is running - schedule pause for after it completes
            new_status = 'PAUSE_PENDING'
            message = f'Pause scheduled - will pause after wave {current_wave_number} completes'
        else:
            # Between waves - pause immediately
            new_status = 'PAUSED'
            message = 'Execution paused'
        
        execution_history_table.update_item(
            Key={'ExecutionId': execution_id, 'PlanId': plan_id},
            UpdateExpression='SET #status = :status',
            ExpressionAttributeNames={'#status': 'Status'},
            ExpressionAttributeValues={':status': new_status}
        )
        
        print(f"Pause execution {execution_id}: status={new_status}, current_wave={current_wave_number}")
        return response(200, {
            'executionId': execution_id,
            'status': new_status,
            'message': message,
            'lastCompletedWave': last_completed_wave
        })
        
    except Exception as e:
        print(f"Error pausing execution: {str(e)}")
        return response(500, {'error': str(e)})


def resume_execution(execution_id: str) -> Dict:
    """Resume a paused execution using Step Functions callback pattern.
    
    Resume is only valid when execution status is PAUSED and has a TaskToken.
    Uses SendTaskSuccess to signal Step Functions to continue from WaitForResume state.
    
    This function:
    1. Validates the execution is paused
    2. Gets the stored TaskToken from DynamoDB
    3. Calls SendTaskSuccess to resume the Step Functions execution
    """
    print(f"=== RESUME_EXECUTION CALLED === execution_id: {execution_id}")
    print(f"Table name: {EXECUTION_HISTORY_TABLE}")
    
    try:
        print(f"Querying DynamoDB for execution {execution_id}...")
        result = execution_history_table.query(
            KeyConditionExpression=Key('ExecutionId').eq(execution_id),
            Limit=1
        )
        print(f"Query result: {json.dumps(result, default=str)}")
        
        if not result.get('Items'):
            print(f"No items found for execution {execution_id}")
            return response(404, {'error': 'Execution not found'})
        
        execution = result['Items'][0]
        plan_id = execution.get('PlanId')
        current_status = execution.get('Status', '')
        
        # Check if execution is paused
        if current_status != 'PAUSED':
            return response(400, {
                'error': 'Execution is not paused',
                'currentStatus': current_status,
                'reason': 'Only paused executions can be resumed'
            })
        
        # Get the stored task token
        task_token = execution.get('TaskToken')
        if not task_token:
            return response(400, {
                'error': 'No task token found',
                'reason': 'Execution is paused but has no task token for callback. This may be a legacy execution.'
            })
        
        # Get paused before wave info
        paused_before_wave = execution.get('PausedBeforeWave', 0)
        # Convert Decimal to int if needed
        if hasattr(paused_before_wave, '__int__'):
            paused_before_wave = int(paused_before_wave)
        
        print(f"Resuming execution {execution_id} from wave {paused_before_wave} using SendTaskSuccess")
        
        # Build the full application state that ResumeWavePlan expects
        # This must match the state structure from orchestration_stepfunctions.py
        # Get the original plan waves (execution history has different structure)
        try:
            plan_response = recovery_plans_table.get_item(Key={'PlanId': plan_id})
            plan_waves = plan_response.get('Item', {}).get('Waves', [])
            # Convert DynamoDB format to plain dicts (handles Decimal types)
            waves_data = json.loads(json.dumps(plan_waves, cls=DecimalEncoder))
            print(f"Loaded {len(waves_data)} waves from recovery plan")
        except Exception as plan_error:
            print(f"Error loading plan waves: {plan_error}")
            return response(500, {'error': f'Failed to load recovery plan: {str(plan_error)}'})
        
        resume_state = {
            'plan_id': plan_id,
            'execution_id': execution_id,
            'is_drill': execution.get('ExecutionType', 'DRILL') == 'DRILL',
            'waves': waves_data,
            'current_wave_number': paused_before_wave,
            'all_waves_completed': False,
            'wave_completed': False,
            'current_wave_update_time': 30,
            'current_wave_total_wait_time': 0,
            'current_wave_max_wait_time': 1800,
            'status': 'running',
            'wave_results': [],
            'job_id': None,
            'region': None,
            'server_ids': [],
            'error': None,
            'paused_before_wave': paused_before_wave
        }
        
        print(f"Resume state: {json.dumps(resume_state, cls=DecimalEncoder)}")
        
        # Call SendTaskSuccess to resume the Step Functions execution
        # The output becomes the state for ResumeWavePlan (no Payload wrapper for callbacks)
        try:
            stepfunctions.send_task_success(
                taskToken=task_token,
                output=json.dumps(resume_state, cls=DecimalEncoder)
            )
            print(f"✅ SendTaskSuccess called for execution {execution_id}")
        except stepfunctions.exceptions.TaskTimedOut:
            return response(400, {
                'error': 'Task timed out',
                'reason': 'The Step Functions task has timed out. The execution may need to be restarted.'
            })
        except stepfunctions.exceptions.InvalidToken:
            return response(400, {
                'error': 'Invalid task token',
                'reason': 'The task token is no longer valid. The execution may have been cancelled or timed out.'
            })
        except Exception as sfn_error:
            print(f"ERROR calling SendTaskSuccess: {str(sfn_error)}")
            return response(500, {'error': f'Failed to resume Step Functions: {str(sfn_error)}'})
        
        # Note: The orchestration Lambda (resume_wave action) will update the status to RUNNING
        # and clear the TaskToken when it processes the resume
        
        wave_display = paused_before_wave + 1  # 0-indexed to 1-indexed for display
        print(f"Resumed execution {execution_id}, wave {wave_display} will start")
        return response(200, {
            'executionId': execution_id,
            'status': 'RESUMING',
            'message': f'Execution resumed - wave {wave_display} will start',
            'nextWave': paused_before_wave
        })
        
    except Exception as e:
        print(f"Error resuming execution: {str(e)}")
        import traceback
        traceback.print_exc()
        return response(500, {'error': str(e)})


def get_job_log_items(execution_id: str, job_id: str = None) -> Dict:
    """Get DRS job log items for an execution's wave.
    
    Returns detailed progress events like:
    - SNAPSHOT_START / SNAPSHOT_END
    - CONVERSION_START / CONVERSION_END  
    - LAUNCH_START / LAUNCH_END
    
    Args:
        execution_id: The execution ID
        job_id: Optional specific job ID. If not provided, returns logs for all waves.
    """
    try:
        # Get execution to find job IDs (use query since table has composite key)
        result = execution_history_table.query(
            KeyConditionExpression=Key('ExecutionId').eq(execution_id),
            Limit=1
        )
        if not result.get('Items'):
            return response(404, {'error': 'Execution not found'})
        
        execution = result['Items'][0]
        waves = execution.get('Waves', [])
        
        all_job_logs = []
        
        for wave in waves:
            wave_job_id = wave.get('JobId') or wave.get('jobId')
            wave_number = wave.get('WaveNumber', wave.get('waveNumber', 0))
            
            # Skip if no job ID or if specific job requested and doesn't match
            if not wave_job_id:
                continue
            if job_id and wave_job_id != job_id:
                continue
            
            try:
                # Get job log items from DRS
                log_response = drs.describe_job_log_items(jobID=wave_job_id)
                log_items = log_response.get('items', [])
                
                # Transform log items for frontend
                wave_logs = {
                    'waveNumber': wave_number,
                    'jobId': wave_job_id,
                    'events': []
                }
                
                for item in log_items:
                    event = {
                        'event': item.get('event', 'UNKNOWN'),
                        'eventData': item.get('eventData', {}),
                        'logDateTime': item.get('logDateTime', '')
                    }
                    
                    # Extract source server info if available
                    event_data = item.get('eventData', {})
                    if 'sourceServerID' in event_data:
                        event['sourceServerId'] = event_data['sourceServerID']
                    if 'rawError' in event_data:
                        event['error'] = event_data['rawError']
                    if 'conversionServerID' in event_data:
                        event['conversionServerId'] = event_data['conversionServerID']
                    
                    wave_logs['events'].append(event)
                
                # Sort events by timestamp (newest first for display)
                wave_logs['events'].sort(
                    key=lambda x: x.get('logDateTime', ''), 
                    reverse=True
                )
                
                all_job_logs.append(wave_logs)
                
            except Exception as e:
                print(f"Error getting job log items for job {wave_job_id}: {e}")
                all_job_logs.append({
                    'waveNumber': wave_number,
                    'jobId': wave_job_id,
                    'events': [],
                    'error': str(e)
                })
        
        return response(200, {
            'executionId': execution_id,
            'jobLogs': all_job_logs
        })
        
    except Exception as e:
        print(f"Error getting job log items: {str(e)}")
        return response(500, {'error': str(e)})


def terminate_recovery_instances(execution_id: str) -> Dict:
    """Terminate all recovery instances from an execution.
    
    This will:
    1. Find all recovery instances created by this execution (from DRS jobs)
    2. Disconnect them from DRS (if applicable)
    3. Terminate the EC2 instances
    
    Only works for executions that have launched recovery instances.
    """
    try:
        # Get execution details
        result = execution_history_table.query(
            KeyConditionExpression=Key('ExecutionId').eq(execution_id),
            Limit=1
        )
        
        if not result.get('Items'):
            return response(404, {'error': 'Execution not found'})
        
        execution = result['Items'][0]
        waves = execution.get('Waves', [])
        
        if not waves:
            return response(400, {
                'error': 'No waves found in execution',
                'reason': 'This execution has no wave data'
            })
        
        # Collect all recovery instance IDs from all waves
        instances_to_terminate = []
        instances_by_region = {}
        
        print(f"Processing {len(waves)} waves for execution {execution_id}")
        
        # Collect source server IDs for alternative lookup
        source_server_ids_by_region = {}
        
        # First, try to get instance IDs from DRS jobs
        for wave in waves:
            wave_number = wave.get('WaveNumber', 0)
            job_id = wave.get('JobId')
            region = wave.get('Region', 'us-east-1')
            wave_status = wave.get('Status', '')
            
            print(f"Wave {wave_number}: status={wave_status}, job_id={job_id}, region={region}")
            
            # Collect source server IDs from wave for alternative lookup
            wave_servers = wave.get('Servers', [])
            for srv in wave_servers:
                srv_id = srv.get('SourceServerId') or srv.get('sourceServerId')
                if srv_id:
                    if region not in source_server_ids_by_region:
                        source_server_ids_by_region[region] = []
                    if srv_id not in source_server_ids_by_region[region]:
                        source_server_ids_by_region[region].append(srv_id)
            
            # Only process waves that have a job ID (were actually launched)
            if job_id and wave_status in ['COMPLETED', 'LAUNCHED', 'PARTIAL']:
                try:
                    drs_client = boto3.client('drs', region_name=region)
                    
                    # Get recovery instances from DRS job
                    job_response = drs_client.describe_jobs(
                        filters={'jobIDs': [job_id]}
                    )
                    
                    print(f"DRS describe_jobs response for {job_id}: {len(job_response.get('items', []))} items")
                    
                    if job_response.get('items'):
                        job = job_response['items'][0]
                        participating_servers = job.get('participatingServers', [])
                        
                        print(f"Job {job_id} has {len(participating_servers)} participating servers")
                        
                        for server in participating_servers:
                            recovery_instance_id = server.get('recoveryInstanceID')
                            source_server_id = server.get('sourceServerID', 'unknown')
                            
                            print(f"Server {source_server_id}: recoveryInstanceID={recovery_instance_id}")
                            
                            # Collect source server ID for alternative lookup
                            if source_server_id and source_server_id != 'unknown':
                                if region not in source_server_ids_by_region:
                                    source_server_ids_by_region[region] = []
                                if source_server_id not in source_server_ids_by_region[region]:
                                    source_server_ids_by_region[region].append(source_server_id)
                            
                            if recovery_instance_id:
                                # Get EC2 instance ID from recovery instance
                                try:
                                    ri_response = drs_client.describe_recovery_instances(
                                        filters={'recoveryInstanceIDs': [recovery_instance_id]}
                                    )
                                    if ri_response.get('items'):
                                        ec2_instance_id = ri_response['items'][0].get('ec2InstanceID')
                                        if ec2_instance_id and ec2_instance_id.startswith('i-'):
                                            instances_to_terminate.append({
                                                'instanceId': ec2_instance_id,
                                                'recoveryInstanceId': recovery_instance_id,
                                                'region': region,
                                                'waveNumber': wave_number,
                                                'serverId': source_server_id,
                                                'jobId': job_id
                                            })
                                            
                                            if region not in instances_by_region:
                                                instances_by_region[region] = []
                                            instances_by_region[region].append(ec2_instance_id)
                                except Exception as ri_err:
                                    print(f"Could not get EC2 instance for recovery instance {recovery_instance_id}: {ri_err}")
                                    
                except Exception as drs_err:
                    print(f"Could not query DRS job {job_id} in {region}: {drs_err}")
        
        # Alternative approach: Query describe_recovery_instances by source server IDs
        # This works even when job's participatingServers doesn't have recoveryInstanceID
        if not instances_to_terminate and source_server_ids_by_region:
            print(f"Trying alternative approach: query recovery instances by source server IDs")
            
            for region, source_ids in source_server_ids_by_region.items():
                print(f"Querying recovery instances for {len(source_ids)} source servers in {region}: {source_ids}")
                
                try:
                    drs_client = boto3.client('drs', region_name=region)
                    
                    # Query recovery instances by source server IDs
                    ri_response = drs_client.describe_recovery_instances(
                        filters={'sourceServerIDs': source_ids}
                    )
                    
                    recovery_instances = ri_response.get('items', [])
                    print(f"Found {len(recovery_instances)} recovery instances for source servers")
                    
                    for ri in recovery_instances:
                        ec2_instance_id = ri.get('ec2InstanceID')
                        recovery_instance_id = ri.get('recoveryInstanceID')
                        source_server_id = ri.get('sourceServerID', 'unknown')
                        
                        print(f"Recovery instance: ec2={ec2_instance_id}, ri={recovery_instance_id}, source={source_server_id}")
                        
                        if ec2_instance_id and ec2_instance_id.startswith('i-'):
                            instances_to_terminate.append({
                                'instanceId': ec2_instance_id,
                                'recoveryInstanceId': recovery_instance_id,
                                'region': region,
                                'waveNumber': 0,  # Unknown wave
                                'serverId': source_server_id
                            })
                            
                            if region not in instances_by_region:
                                instances_by_region[region] = []
                            if ec2_instance_id not in instances_by_region[region]:
                                instances_by_region[region].append(ec2_instance_id)
                                
                except Exception as e:
                    print(f"Error querying recovery instances by source server IDs in {region}: {e}")
        
        # Fallback: check stored data in ServerStatuses or Servers
        if not instances_to_terminate:
            for wave in waves:
                wave_number = wave.get('WaveNumber', 0)
                region = wave.get('Region', 'us-east-1')
                
                # Check ServerStatuses (newer format)
                server_statuses = wave.get('ServerStatuses', [])
                for server in server_statuses:
                    instance_id = (
                        server.get('RecoveryInstanceID') or 
                        server.get('recoveryInstanceId') or
                        server.get('EC2InstanceId') or
                        server.get('ec2InstanceId')
                    )
                    if instance_id and isinstance(instance_id, str) and instance_id.startswith('i-'):
                        instances_to_terminate.append({
                            'instanceId': instance_id,
                            'region': region,
                            'waveNumber': wave_number,
                            'serverId': server.get('SourceServerId', 'unknown')
                        })
                        if region not in instances_by_region:
                            instances_by_region[region] = []
                        instances_by_region[region].append(instance_id)
                
                # Check Servers (older format)
                servers = wave.get('Servers', [])
                for server in servers:
                    instance_id = (
                        server.get('RecoveryInstanceId') or 
                        server.get('recoveryInstanceId') or
                        server.get('InstanceId') or
                        server.get('instanceId') or
                        server.get('ec2InstanceId') or
                        server.get('EC2InstanceId')
                    )
                    if instance_id and isinstance(instance_id, str) and instance_id.startswith('i-'):
                        server_region = server.get('Region', region)
                        instances_to_terminate.append({
                            'instanceId': instance_id,
                            'region': server_region,
                            'waveNumber': wave_number,
                            'serverId': server.get('SourceServerId', 'unknown')
                        })
                        if server_region not in instances_by_region:
                            instances_by_region[server_region] = []
                        instances_by_region[server_region].append(instance_id)
        
        if not instances_to_terminate:
            return response(400, {
                'error': 'No recovery instances found',
                'reason': 'This execution has no recovery instances to terminate. Instances may not have been launched yet, may have already been terminated, or the DRS job data is unavailable.'
            })
        
        print(f"Found {len(instances_to_terminate)} recovery instances to terminate")
        
        # Group recovery instance IDs by region for DRS API call
        recovery_instances_by_region = {}
        for instance_info in instances_to_terminate:
            region = instance_info.get('region', 'us-east-1')
            # The recovery instance ID is the same as the EC2 instance ID in DRS
            recovery_instance_id = instance_info.get('recoveryInstanceId') or instance_info.get('instanceId')
            if recovery_instance_id:
                if region not in recovery_instances_by_region:
                    recovery_instances_by_region[region] = []
                if recovery_instance_id not in recovery_instances_by_region[region]:
                    recovery_instances_by_region[region].append(recovery_instance_id)
        
        # Use DRS TerminateRecoveryInstances API - this properly terminates via DRS
        # and creates a TERMINATE job in DRS console
        terminated = []
        failed = []
        jobs_created = []
        
        for region, recovery_instance_ids in recovery_instances_by_region.items():
            try:
                drs_client = boto3.client('drs', region_name=region)
                
                print(f"Calling DRS TerminateRecoveryInstances for {len(recovery_instance_ids)} instances in {region}: {recovery_instance_ids}")
                
                # Call DRS TerminateRecoveryInstances API
                # This creates a TERMINATE job and properly cleans up in DRS
                terminate_response = drs_client.terminate_recovery_instances(
                    recoveryInstanceIDs=recovery_instance_ids
                )
                
                # Get the job info from response
                job = terminate_response.get('job', {})
                job_id = job.get('jobID')
                
                if job_id:
                    jobs_created.append({
                        'jobId': job_id,
                        'region': region,
                        'type': job.get('type', 'TERMINATE'),
                        'status': job.get('status', 'PENDING')
                    })
                    print(f"Created DRS terminate job: {job_id}")
                
                # Track terminated instances
                for ri_id in recovery_instance_ids:
                    terminated.append({
                        'recoveryInstanceId': ri_id,
                        'region': region,
                        'jobId': job_id
                    })
                    
            except drs_client.exceptions.ConflictException as e:
                # Instances already being terminated or don't exist
                error_msg = str(e)
                print(f"ConflictException terminating recovery instances in {region}: {error_msg}")
                for ri_id in recovery_instance_ids:
                    failed.append({
                        'recoveryInstanceId': ri_id,
                        'region': region,
                        'error': 'Already terminated or being processed',
                        'errorType': 'CONFLICT'
                    })
            except Exception as e:
                error_msg = str(e)
                print(f"Error terminating recovery instances in {region}: {error_msg}")
                for ri_id in recovery_instance_ids:
                    failed.append({
                        'recoveryInstanceId': ri_id,
                        'region': region,
                        'error': error_msg
                    })
        
        print(f"Terminated {len(terminated)} recovery instances via DRS API")
        
        # Update execution with termination info
        try:
            plan_id = execution.get('PlanId')
            execution_history_table.update_item(
                Key={'ExecutionId': execution_id, 'PlanId': plan_id},
                UpdateExpression='SET InstancesTerminated = :terminated, InstancesTerminatedAt = :timestamp, TerminateJobs = :jobs',
                ExpressionAttributeValues={
                    ':terminated': True,
                    ':timestamp': int(time.time()),
                    ':jobs': jobs_created
                }
            )
        except Exception as e:
            print(f"Warning: Could not update execution with termination status: {str(e)}")
        
        # Check if all failures are due to conflict (already terminated)
        all_conflict = len(failed) > 0 and all(f.get('errorType') == 'CONFLICT' for f in failed)
        
        if len(terminated) == 0 and all_conflict:
            # All instances already terminated or being processed
            return response(200, {
                'executionId': execution_id,
                'message': 'Recovery instances already terminated or being processed',
                'terminated': terminated,
                'failed': failed,
                'jobs': jobs_created,
                'totalFound': len(instances_to_terminate),
                'totalTerminated': len(terminated),
                'totalFailed': len(failed),
                'alreadyTerminated': True
            })
        
        return response(200, {
            'executionId': execution_id,
            'message': f'Initiated termination of {len(terminated)} recovery instances via DRS',
            'terminated': terminated,
            'failed': failed,
            'jobs': jobs_created,
            'totalFound': len(instances_to_terminate),
            'totalTerminated': len(terminated),
            'totalFailed': len(failed)
        })
        
    except Exception as e:
        print(f"Error terminating recovery instances: {str(e)}")
        import traceback
        traceback.print_exc()
        return response(500, {'error': str(e)})


def delete_completed_executions() -> Dict:
    """
    Delete all completed executions (terminal states only)
    
    Safe operation that only removes:
    - COMPLETED executions
    - PARTIAL executions (some servers failed)
    - FAILED executions
    - CANCELLED executions
    
    Active executions (PENDING, POLLING, INITIATED, LAUNCHING, IN_PROGRESS, RUNNING) are preserved.
    """
    try:
        print("Starting bulk delete of completed executions")
        
        # Define terminal states that are safe to delete
        # Only delete truly completed executions, NOT active ones
        terminal_states = ['COMPLETED', 'PARTIAL', 'FAILED', 'CANCELLED', 'TIMEOUT']
        # Active states to preserve (never delete)
        active_states = ['PENDING', 'POLLING', 'INITIATED', 'LAUNCHING', 'STARTED', 'IN_PROGRESS', 'RUNNING', 'PAUSED']
        
        # Scan for all executions
        scan_result = execution_history_table.scan()
        all_executions = scan_result.get('Items', [])
        
        # Handle pagination if there are more results
        while 'LastEvaluatedKey' in scan_result:
            scan_result = execution_history_table.scan(
                ExclusiveStartKey=scan_result['LastEvaluatedKey']
            )
            all_executions.extend(scan_result.get('Items', []))
        
        print(f"Found {len(all_executions)} total executions")
        
        # Filter to only completed executions
        completed_executions = [
            ex for ex in all_executions 
            if ex.get('Status', '').upper() in terminal_states
        ]
        
        print(f"Found {len(completed_executions)} completed executions to delete")
        
        # Delete completed executions (DynamoDB requires ExecutionId + PlanId for delete)
        deleted_count = 0
        failed_deletes = []
        
        for execution in completed_executions:
            execution_id = execution.get('ExecutionId')
            plan_id = execution.get('PlanId')
            
            if not execution_id or not plan_id:
                print(f"Skipping execution with missing keys: {execution}")
                continue
            
            try:
                execution_history_table.delete_item(
                    Key={
                        'ExecutionId': execution_id,
                        'PlanId': plan_id
                    }
                )
                deleted_count += 1
                print(f"Deleted execution: {execution_id}")
            except Exception as delete_error:
                error_msg = str(delete_error)
                print(f"Failed to delete execution {execution_id}: {error_msg}")
                failed_deletes.append({
                    'executionId': execution_id,
                    'error': error_msg
                })
        
        # Build response
        result = {
            'message': 'Completed executions cleared successfully',
            'deletedCount': deleted_count,
            'totalScanned': len(all_executions),
            'completedFound': len(completed_executions),
            'activePreserved': len(all_executions) - len(completed_executions)
        }
        
        if failed_deletes:
            result['failedDeletes'] = failed_deletes
            result['warning'] = f'{len(failed_deletes)} execution(s) failed to delete'
        
        print(f"Bulk delete completed: {deleted_count} deleted, {len(failed_deletes)} failed")
        return response(200, result)
        
    except Exception as e:
        print(f"Error deleting completed executions: {str(e)}")
        import traceback
        traceback.print_exc()
        return response(500, {
            'error': 'DELETE_FAILED',
            'message': f'Failed to delete completed executions: {str(e)}'
        })


# ============================================================================
# DRS Source Servers Handler (AUTOMATIC DISCOVERY)
# ============================================================================

def handle_drs_source_servers(query_params: Dict) -> Dict:
    """Route DRS source servers discovery requests"""
    region = query_params.get('region')
    current_pg_id = query_params.get('currentProtectionGroupId')
    filter_by_pg = query_params.get('filterByProtectionGroup')  # NEW: Filter mode
    
    if not region:
        return response(400, {'error': 'region parameter is required'})
    
    # NEW: If filtering by PG, return only that PG's servers
    if filter_by_pg:
        return get_protection_group_servers(filter_by_pg, region)
    
    return list_source_servers(region, current_pg_id)


def list_source_servers(region: str, current_pg_id: Optional[str] = None) -> Dict:
    """
    Discover DRS source servers in a region and track assignments
    
    Returns:
    - All DRS source servers in region
    - Assignment status for each server
    - DRS initialization status
    """
    print(f"Listing source servers for region: {region}")
    
    try:
        # 1. Query DRS for source servers
        drs_client = boto3.client('drs', region_name=region)
        
        try:
            servers_response = drs_client.describe_source_servers(maxResults=200)
            drs_initialized = True
        except drs_client.exceptions.UninitializedAccountException:
            print(f"DRS not initialized in {region}")
            return response(400, {
                'error': 'DRS_NOT_INITIALIZED',
                'message': f'AWS Elastic Disaster Recovery (DRS) is not initialized in {region}. Go to the DRS Console in {region} and complete the initialization wizard before creating Protection Groups.',
                'region': region,
                'initialized': False
            })
        except Exception as e:
            print(f"Error querying DRS: {str(e)}")
            # Check if it's an uninitialized error by message
            if 'UninitializedAccountException' in str(e) or 'not initialized' in str(e).lower():
                return response(400, {
                    'error': 'DRS_NOT_INITIALIZED',
                    'message': f'AWS Elastic Disaster Recovery (DRS) is not initialized in {region}. Go to the DRS Console in {region} and complete the initialization wizard before creating Protection Groups.',
                    'region': region,
                    'initialized': False
                })
            raise
        
        # 2. Build server list from DRS response
        servers = []
        source_instance_ids = []  # Collect instance IDs for EC2 tag lookup
        
        for item in servers_response.get('items', []):
            server_id = item['sourceServerID']
            
            # Extract server metadata
            source_props = item.get('sourceProperties', {})
            ident_hints = source_props.get('identificationHints', {})
            hostname = ident_hints.get('hostname', 'Unknown')
            
            # Extract source instance details
            source_instance_id = ident_hints.get('awsInstanceID', '')
            if source_instance_id:
                source_instance_ids.append(source_instance_id)
            
            # Extract source IP from network interfaces
            network_interfaces = source_props.get('networkInterfaces', [])
            source_ip = ''
            if network_interfaces:
                ips = network_interfaces[0].get('ips', [])
                if ips:
                    source_ip = ips[0]
            
            # Extract OS info
            os_info = source_props.get('os', {})
            os_string = os_info.get('fullString', '')
            
            # Extract source region from sourceCloudProperties
            source_cloud_props = item.get('sourceCloudProperties', {})
            source_region = source_cloud_props.get('originRegion', '')
            source_account = source_cloud_props.get('originAccountID', '')
            
            # Extract replication info
            lifecycle = item.get('lifeCycle', {})
            
            data_rep_info = item.get('dataReplicationInfo', {})
            rep_state = data_rep_info.get('dataReplicationState', 'UNKNOWN')
            lag_duration = data_rep_info.get('lagDuration', 'UNKNOWN')
            
            # Map replication state to lifecycle state for display
            state_mapping = {
                'STOPPED': 'STOPPED',
                'INITIATING': 'INITIATING',
                'INITIAL_SYNC': 'SYNCING',
                'BACKLOG': 'SYNCING',
                'CREATING_SNAPSHOT': 'SYNCING',
                'CONTINUOUS': 'READY_FOR_RECOVERY',
                'PAUSED': 'PAUSED',
                'RESCAN': 'SYNCING',
                'STALLED': 'STALLED',
                'DISCONNECTED': 'DISCONNECTED'
            }
            display_state = state_mapping.get(rep_state, rep_state)
            
            servers.append({
                'sourceServerID': server_id,
                'hostname': hostname,
                'nameTag': '',  # Will be populated from EC2 below
                'sourceInstanceId': source_instance_id,
                'sourceIp': source_ip,
                'sourceRegion': source_region,
                'sourceAccount': source_account,
                'os': os_string,
                'state': display_state,
                'replicationState': rep_state,
                'lagDuration': lag_duration,
                'lastSeen': lifecycle.get('lastSeenByServiceDateTime', ''),
                'assignedToProtectionGroup': None,  # Will be populated below
                'selectable': True  # Will be updated below
            })
        
        # 2b. Fetch Name tags from source EC2 instances
        ec2_name_tags = {}
        if source_instance_ids:
            try:
                ec2_client = boto3.client('ec2', region_name=region)
                ec2_response = ec2_client.describe_instances(InstanceIds=source_instance_ids)
                for reservation in ec2_response.get('Reservations', []):
                    for instance in reservation.get('Instances', []):
                        instance_id = instance.get('InstanceId', '')
                        for tag in instance.get('Tags', []):
                            if tag.get('Key') == 'Name':
                                ec2_name_tags[instance_id] = tag.get('Value', '')
                                break
            except Exception as e:
                print(f"Warning: Could not fetch EC2 tags: {str(e)}")
        
        # Update servers with EC2 Name tags
        for server in servers:
            if server['sourceInstanceId'] in ec2_name_tags:
                server['nameTag'] = ec2_name_tags[server['sourceInstanceId']]
        
        # 3. Query ALL Protection Groups to build assignment map
        # Exclude current PG if editing (allows deselection)
        pg_response = protection_groups_table.scan()
        
        assignment_map = {}
        for pg in pg_response.get('Items', []):
            pg_id = pg.get('GroupId') or pg.get('protectionGroupId')
            
            # Skip current PG when editing - allows deselection
            if current_pg_id and pg_id == current_pg_id:
                continue
            
            pg_name = pg.get('GroupName') or pg.get('name')
            pg_servers = pg.get('SourceServerIds') or pg.get('sourceServerIds', [])
            
            for server_id in pg_servers:
                assignment_map[server_id] = {
                    'protectionGroupId': pg_id,
                    'protectionGroupName': pg_name
                }
        
        # 4. Update servers with assignment info
        for server in servers:
            server_id = server['sourceServerID']
            if server_id in assignment_map:
                server['assignedToProtectionGroup'] = assignment_map[server_id]
                server['selectable'] = False
        
        # 5. Return enhanced server list
        return response(200, {
            'region': region,
            'initialized': True,
            'servers': servers,
            'totalCount': len(servers),
            'availableCount': sum(1 for s in servers if s['selectable']),
            'assignedCount': sum(1 for s in servers if not s['selectable'])
        })
        
    except Exception as e:
        print(f"Error listing source servers: {str(e)}")
        import traceback
        traceback.print_exc()
        return response(500, {
            'error': 'INTERNAL_ERROR',
            'message': f'Failed to list source servers: {str(e)}'
        })


def get_protection_group_servers(pg_id: str, region: str) -> Dict:
    """
    Get servers that belong to a specific Protection Group
    
    Args:
    - pg_id: Protection Group ID
    - region: AWS region
    
    Returns:
    - Response with servers from the Protection Group
    """
    print(f"Getting servers for Protection Group: {pg_id}")
    
    try:
        # 1. Get the Protection Group
        result = protection_groups_table.get_item(Key={'GroupId': pg_id})
        
        if 'Item' not in result:
            return response(404, {
                'error': 'PROTECTION_GROUP_NOT_FOUND',
                'message': f'Protection Group {pg_id} not found'
            })
        
        pg = result['Item']
        pg_server_ids = pg.get('SourceServerIds', [])
        
        if not pg_server_ids:
            return response(200, {
                'region': region,
                'protectionGroupId': pg_id,
                'protectionGroupName': pg.get('GroupName'),
                'initialized': True,
                'servers': [],
                'totalCount': 0
            })
        
        # 2. Query DRS for these specific servers
        drs_client = boto3.client('drs', region_name=region)
        
        try:
            servers_response = drs_client.describe_source_servers(
                filters={
                    'sourceServerIDs': pg_server_ids
                }
            )
        except drs_client.exceptions.UninitializedAccountException:
            return response(400, {
                'error': 'DRS_NOT_INITIALIZED',
                'message': f'DRS is not initialized in {region}',
                'region': region,
                'initialized': False
            })
        except Exception as e:
            print(f"Error querying DRS: {str(e)}")
            if 'UninitializedAccountException' in str(e) or 'not initialized' in str(e).lower():
                return response(400, {
                    'error': 'DRS_NOT_INITIALIZED',
                    'message': f'DRS is not initialized in {region}',
                    'region': region,
                    'initialized': False
                })
            raise
        
        # 3. Build server list from DRS response
        servers = []
        for item in servers_response.get('items', []):
            server_id = item['sourceServerID']
            
            # Extract server metadata
            source_props = item.get('sourceProperties', {})
            ident_hints = source_props.get('identificationHints', {})
            hostname = ident_hints.get('hostname', 'Unknown')
            
            # Extract replication info
            lifecycle = item.get('lifeCycle', {})
            data_rep_info = item.get('dataReplicationInfo', {})
            rep_state = data_rep_info.get('dataReplicationState', 'UNKNOWN')
            lag_duration = data_rep_info.get('lagDuration', 'UNKNOWN')
            
            # Map replication state to lifecycle state for display
            state_mapping = {
                'STOPPED': 'STOPPED',
                'INITIATING': 'INITIATING',
                'INITIAL_SYNC': 'SYNCING',
                'BACKLOG': 'SYNCING',
                'CREATING_SNAPSHOT': 'SYNCING',
                'CONTINUOUS': 'READY_FOR_RECOVERY',
                'PAUSED': 'PAUSED',
                'RESCAN': 'SYNCING',
                'STALLED': 'STALLED',
                'DISCONNECTED': 'DISCONNECTED'
            }
            display_state = state_mapping.get(rep_state, rep_state)
            
            servers.append({
                'sourceServerID': server_id,
                'hostname': hostname,
                'state': display_state,
                'replicationState': rep_state,
                'lagDuration': lag_duration,
                'lastSeen': lifecycle.get('lastSeenByServiceDateTime', ''),
                'assignedToProtectionGroup': {
                    'protectionGroupId': pg_id,
                    'protectionGroupName': pg.get('GroupName')
                },
                'selectable': True  # All servers in this PG are selectable for waves
            })
        
        # 4. Return server list
        return response(200, {
            'region': region,
            'protectionGroupId': pg_id,
            'protectionGroupName': pg.get('GroupName'),
            'initialized': True,
            'servers': servers,
            'totalCount': len(servers)
        })
        
    except Exception as e:
        print(f"Error getting Protection Group servers: {str(e)}")
        import traceback
        traceback.print_exc()
        return response(500, {
            'error': 'INTERNAL_ERROR',
            'message': f'Failed to get Protection Group servers: {str(e)}'
        })


def validate_server_assignments(server_ids: List[str], current_pg_id: Optional[str] = None) -> List[Dict]:
    """
    Validate that servers are not already assigned to other Protection Groups
    
    Args:
    - server_ids: List of server IDs to validate
    - current_pg_id: Optional PG ID to exclude (for edit operations)
    
    Returns:
    - conflicts: List of {serverId, protectionGroupId, protectionGroupName}
    """
    pg_response = protection_groups_table.scan()
    
    conflicts = []
    for pg in pg_response.get('Items', []):
        pg_id = pg.get('GroupId') or pg.get('protectionGroupId')
        
        # Skip current PG when editing
        if current_pg_id and pg_id == current_pg_id:
            continue
        
        assigned_servers = pg.get('SourceServerIds') or pg.get('sourceServerIds', [])
        for server_id in server_ids:
            if server_id in assigned_servers:
                pg_name = pg.get('GroupName') or pg.get('name')
                conflicts.append({
                    'serverId': server_id,
                    'protectionGroupId': pg_id,
                    'protectionGroupName': pg_name
                })
    
    return conflicts


def validate_servers_exist_in_drs(region: str, server_ids: List[str]) -> List[str]:
    """
    Validate that server IDs actually exist in DRS
    
    Args:
    - region: AWS region to check
    - server_ids: List of server IDs to validate
    
    Returns:
    - List of invalid server IDs (empty list if all valid)
    """
    try:
        drs_client = boto3.client('drs', region_name=region)
        
        # Get all source servers in the region
        response = drs_client.describe_source_servers(maxResults=200)
        valid_server_ids = {s['sourceServerID'] for s in response.get('items', [])}
        
        # Find invalid servers
        invalid_servers = [sid for sid in server_ids if sid not in valid_server_ids]
        
        if invalid_servers:
            print(f"Invalid server IDs detected: {invalid_servers}")
        
        return invalid_servers
        
    except Exception as e:
        print(f"Error validating servers in DRS: {str(e)}")
        # On error, assume servers might be valid (fail open for now)
        # In production, might want to fail closed
        return []


def validate_unique_pg_name(name: str, current_pg_id: Optional[str] = None) -> bool:
    """
    Validate that Protection Group name is unique (case-insensitive)
    
    Args:
    - name: Protection Group name to validate
    - current_pg_id: Optional PG ID to exclude (for edit operations)
    
    Returns:
    - True if unique, False if duplicate exists
    """
    pg_response = protection_groups_table.scan()
    
    name_lower = name.lower()
    for pg in pg_response.get('Items', []):
        pg_id = pg.get('GroupId') or pg.get('protectionGroupId')
        
        # Skip current PG when editing
        if current_pg_id and pg_id == current_pg_id:
            continue
        
        existing_name = pg.get('GroupName') or pg.get('name', '')
        if existing_name.lower() == name_lower:
            return False
    
    return True


def validate_unique_rp_name(name: str, current_rp_id: Optional[str] = None) -> bool:
    """
    Validate that Recovery Plan name is unique (case-insensitive)
    
    Args:
    - name: Recovery Plan name to validate
    - current_rp_id: Optional RP ID to exclude (for edit operations)
    
    Returns:
    - True if unique, False if duplicate exists
    """
    rp_response = recovery_plans_table.scan()
    
    name_lower = name.lower()
    for rp in rp_response.get('Items', []):
        rp_id = rp.get('PlanId')
        
        # Skip current RP when editing
        if current_rp_id and rp_id == current_rp_id:
            continue
        
        existing_name = rp.get('PlanName', '')
        if existing_name.lower() == name_lower:
            return False
    
    return True


# ============================================================================
# Helper Functions
# ============================================================================

def transform_pg_to_camelcase(pg: Dict) -> Dict:
    """Transform Protection Group from DynamoDB PascalCase to frontend camelCase"""
    # Convert timestamps from seconds to milliseconds for JavaScript Date()
    created_at = pg.get('CreatedDate')
    updated_at = pg.get('LastModifiedDate')
    
    return {
        'protectionGroupId': pg.get('GroupId'),
        'name': pg.get('GroupName'),
        'description': pg.get('Description', ''),
        'region': pg.get('Region'),
        'sourceServerIds': pg.get('SourceServerIds', []),
        'accountId': pg.get('AccountId', ''),
        'owner': pg.get('Owner', ''),
        'createdAt': int(created_at * 1000) if created_at else None,
        'updatedAt': int(updated_at * 1000) if updated_at else None,
        'serverDetails': pg.get('ServerDetails', [])
    }


def transform_rp_to_camelcase(rp: Dict) -> Dict:
    """Transform Recovery Plan from DynamoDB PascalCase to frontend camelCase"""
    
    # Determine plan status based on execution history
    # - 'draft' if never executed (no LastExecutedDate)
    # - 'active' if has been executed
    status = 'active' if rp.get('LastExecutedDate') else 'draft'
    
    # Transform waves array from backend PascalCase to frontend camelCase
    waves = []
    for idx, wave in enumerate(rp.get('Waves', [])):
        # CRITICAL FIX: Defensive ServerIds extraction with recovery logic
        server_ids = wave.get('ServerIds', [])
        
        # DEFENSIVE: Ensure we have a list (boto3 deserialization issue)
        if not isinstance(server_ids, list):
            print(f"ERROR: ServerIds is not a list for wave {idx}, got type {type(server_ids)}: {server_ids}")
            # Attempt recovery: wrap in list if string, empty list otherwise
            if isinstance(server_ids, str):
                server_ids = [server_ids]
            else:
                server_ids = []
        
        # Extract dependency wave numbers from WaveId format
        depends_on_waves = []
        for dep in wave.get('Dependencies', []):
            wave_id = dep.get('DependsOnWaveId', '')
            if wave_id and '-' in wave_id:
                try:
                    wave_num = int(wave_id.split('-')[-1])
                    depends_on_waves.append(wave_num)
                except (ValueError, IndexError) as e:
                    print(f"WARNING: Failed to parse dependency wave ID '{wave_id}': {e}")
        
        waves.append({
            'waveNumber': idx,
            'name': wave.get('WaveName', ''),
            'description': wave.get('WaveDescription', ''),
            'serverIds': server_ids,  # Now guaranteed to be a list
            'executionType': wave.get('ExecutionType', 'sequential'),
            'dependsOnWaves': depends_on_waves,
            'protectionGroupId': wave.get('ProtectionGroupId'),  # camelCase for frontend
            'protectionGroupIds': [wave.get('ProtectionGroupId')] if wave.get('ProtectionGroupId') else [],  # Array format
            'pauseBeforeWave': wave.get('PauseBeforeWave', False)  # Pause before starting this wave
        })
    
    # Convert timestamps from seconds to milliseconds for JavaScript Date()
    created_at = rp.get('CreatedDate')
    updated_at = rp.get('LastModifiedDate')
    last_executed_at = rp.get('LastExecutedDate')
    last_start_time = rp.get('LastStartTime')
    last_end_time = rp.get('LastEndTime')
    
    # Transform conflict info if present
    conflict_info = rp.get('ConflictInfo')
    transformed_conflict = None
    if conflict_info:
        transformed_conflict = {
            'hasConflict': conflict_info.get('hasConflict', False),
            'conflictingServers': conflict_info.get('conflictingServers', []),
            'conflictingExecutionId': conflict_info.get('conflictingExecutionId'),
            'conflictingPlanId': conflict_info.get('conflictingPlanId'),
            'conflictingStatus': conflict_info.get('conflictingStatus'),
            'reason': conflict_info.get('reason')
        }
    
    return {
        'id': rp.get('PlanId'),
        'name': rp.get('PlanName'),
        'description': rp.get('Description', ''),
        'status': status,  # NEW: Draft if never executed, Active if executed
        'accountId': rp.get('AccountId'),
        'region': rp.get('Region'),
        'owner': rp.get('Owner'),
        'rpo': rp.get('RPO'),
        'rto': rp.get('RTO'),
        'waves': waves,  # Now properly transformed
        'createdAt': int(created_at * 1000) if created_at else None,
        'updatedAt': int(updated_at * 1000) if updated_at else None,
        'lastExecutedAt': int(last_executed_at * 1000) if last_executed_at else None,
        'lastExecutionStatus': rp.get('LastExecutionStatus'),  # NEW: Execution status
        'lastStartTime': last_start_time,  # NEW: Unix timestamp (seconds) - no conversion needed
        'lastEndTime': last_end_time,  # NEW: Unix timestamp (seconds) - no conversion needed
        'waveCount': len(waves),
        'hasServerConflict': rp.get('HasServerConflict', False),  # NEW: Server conflict with other executions
        'conflictInfo': transformed_conflict  # NEW: Details about the conflict
    }


def transform_execution_to_camelcase(execution: Dict) -> Dict:
    """Transform Execution from DynamoDB PascalCase to frontend camelCase"""
    
    # Helper function to safely convert timestamp (string or int) to int
    def safe_timestamp_to_int(value):
        if value is None:
            return None
        try:
            # Handle both string and int types
            return int(value) if value else None
        except (ValueError, TypeError):
            print(f"WARNING: Invalid timestamp value: {value}")
            return None
    
    # Helper function to map execution status
    def map_execution_status(status):
        """Map backend status to frontend display status"""
        if not status:
            return 'unknown'
        
        status_upper = status.upper()
        
        # Map status for frontend display - PRESERVES DRS TERMINOLOGY
        status_mapping = {
            # Orchestration states
            'PENDING': 'pending',
            'POLLING': 'polling',
            'INITIATED': 'initiated',  # FIXED: Preserve DRS status name
            'LAUNCHING': 'launching',  # FIXED: Preserve DRS status name
            
            # DRS job states
            'STARTED': 'started',  # NEW: DRS job active status
            'IN_PROGRESS': 'in_progress',
            'RUNNING': 'running',
            
            # Terminal states
            'COMPLETED': 'completed',
            'PARTIAL': 'partial',  # Some servers failed
            'FAILED': 'failed',
            'CANCELLED': 'cancelled',
            'PAUSED': 'paused'
        }

        return status_mapping.get(status_upper, status.lower())
    
    # Transform waves array to camelCase
    waves = []
    for wave in execution.get('Waves', []):
        # Transform servers array to camelCase
        # FIX: DynamoDB stores ServerStatuses (from Step Functions) or ServerIds (legacy)
        servers = []
        
        # Build enriched server lookup map from EnrichedServers (added by enrich_execution_with_server_details)
        enriched_map = {}
        for enriched in wave.get('EnrichedServers', []):
            enriched_map[enriched.get('SourceServerId')] = enriched
        
        # First try ServerStatuses (new format from Step Functions orchestration)
        server_statuses = wave.get('ServerStatuses', [])
        if server_statuses:
            for server in server_statuses:
                server_id = server.get('SourceServerId')
                enriched = enriched_map.get(server_id, {})
                servers.append({
                    'sourceServerId': server_id,
                    'recoveryJobId': wave.get('JobId'),  # JobId is at wave level
                    'instanceId': server.get('RecoveryInstanceID'),
                    'status': server.get('LaunchStatus', 'UNKNOWN'),
                    'launchTime': safe_timestamp_to_int(wave.get('StartTime')),
                    'error': server.get('Error'),
                    # Enriched fields from DRS source server
                    'hostname': enriched.get('Hostname', ''),
                    'serverName': enriched.get('NameTag', ''),
                    'region': enriched.get('Region', wave.get('Region', '')),
                    'sourceInstanceId': enriched.get('SourceInstanceId', ''),
                    'sourceAccountId': enriched.get('SourceAccountId', ''),
                    'sourceIp': enriched.get('SourceIp', ''),
                    'sourceRegion': enriched.get('SourceRegion', ''),
                    'replicationState': enriched.get('ReplicationState', ''),
                })
        else:
            # Fallback to ServerIds (legacy format) or Servers array
            server_ids = wave.get('ServerIds', [])
            legacy_servers = wave.get('Servers', [])
            
            if legacy_servers:
                # Use legacy Servers array format
                for server in legacy_servers:
                    server_id = server.get('SourceServerId')
                    enriched = enriched_map.get(server_id, {})
                    servers.append({
                        'sourceServerId': server_id,
                        'recoveryJobId': server.get('RecoveryJobId'),
                        'instanceId': server.get('InstanceId'),
                        'status': server.get('Status', 'UNKNOWN'),
                        'launchTime': safe_timestamp_to_int(server.get('LaunchTime')),
                        'error': server.get('Error'),
                        # Enriched fields from DRS source server
                        'hostname': enriched.get('Hostname', ''),
                        'serverName': enriched.get('NameTag', ''),
                        'region': enriched.get('Region', wave.get('Region', '')),
                        'sourceInstanceId': enriched.get('SourceInstanceId', ''),
                        'sourceAccountId': enriched.get('SourceAccountId', ''),
                        'sourceIp': enriched.get('SourceIp', ''),
                        'sourceRegion': enriched.get('SourceRegion', ''),
                        'replicationState': enriched.get('ReplicationState', ''),
                    })
            elif server_ids:
                # Build servers from ServerIds list (minimal info)
                for server_id in server_ids:
                    enriched = enriched_map.get(server_id, {})
                    servers.append({
                        'sourceServerId': server_id,
                        'recoveryJobId': wave.get('JobId'),
                        'instanceId': None,
                        'status': wave.get('Status', 'UNKNOWN'),  # Use wave status
                        'launchTime': safe_timestamp_to_int(wave.get('StartTime')),
                        'error': None,
                        # Enriched fields from DRS source server
                        'hostname': enriched.get('Hostname', ''),
                        'serverName': enriched.get('NameTag', ''),
                        'region': enriched.get('Region', wave.get('Region', '')),
                        'sourceInstanceId': enriched.get('SourceInstanceId', ''),
                        'sourceAccountId': enriched.get('SourceAccountId', ''),
                        'sourceIp': enriched.get('SourceIp', ''),
                        'sourceRegion': enriched.get('SourceRegion', ''),
                        'replicationState': enriched.get('ReplicationState', ''),
                    })
        
        waves.append({
            'waveName': wave.get('WaveName'),
            'protectionGroupId': wave.get('ProtectionGroupId'),
            'region': wave.get('Region'),
            'status': map_execution_status(wave.get('Status')),  # Use status mapping
            'servers': servers,
            'startTime': safe_timestamp_to_int(wave.get('StartTime')),
            'endTime': safe_timestamp_to_int(wave.get('EndTime')),
            'jobId': wave.get('JobId'),  # DRS job ID for display
        })
    
    # CRITICAL FIX: Convert string timestamps to integers for JavaScript Date()
    start_time = safe_timestamp_to_int(execution.get('StartTime'))
    end_time = safe_timestamp_to_int(execution.get('EndTime'))
    
    # Calculate current wave progress
    # Use stored TotalWaves if available (set at execution creation), otherwise calculate from waves array
    total_waves = execution.get('TotalWaves') or len(waves) or 1
    current_wave = 0
    
    # Find the first wave that's not completed
    for i, wave in enumerate(waves, 1):
        wave_status = wave.get('status', '').lower()
        if wave_status in ['polling', 'initiated', 'launching', 'in_progress', 'started', 'pending']:
            current_wave = i
            break
        elif wave_status == 'completed':
            current_wave = i  # Last completed wave
    
    # If all completed or no waves, current = total
    if current_wave == 0:
        current_wave = max(1, len(waves))  # At least 1 if waves exist
    
    return {
        'executionId': execution.get('ExecutionId'),
        'recoveryPlanId': execution.get('PlanId'),
        'recoveryPlanName': execution.get('RecoveryPlanName', 'Unknown'),
        'executionType': execution.get('ExecutionType'),
        'status': map_execution_status(execution.get('Status')),  # CRITICAL FIX: Map PARTIAL → failed
        'startTime': start_time,  # Now properly converted to int
        'endTime': end_time,  # Now properly converted to int
        'initiatedBy': execution.get('InitiatedBy'),
        'waves': waves,  # Now properly transformed with fixed timestamps and status
        'currentWave': current_wave,  # FIXED: Proper wave progress calculation
        'totalWaves': total_waves,  # Use stored value from execution creation
        'errorMessage': execution.get('ErrorMessage'),
        'pausedBeforeWave': execution.get('PausedBeforeWave')  # Wave number paused before (0-indexed)
    }


def validate_and_get_source_servers(account_id: str, region: str, tags: Dict) -> List[str]:
    """Validate source servers exist with specified tags and return their IDs"""
    try:
        # For now, use current account credentials
        # In production, would assume cross-account role
        drs_client = boto3.client('drs', region_name=region)
        
        # Get all source servers
        servers_response = drs_client.describe_source_servers()
        servers = servers_response.get('items', [])
        
        # Filter by tags
        matching_servers = []
        key_name = tags.get('KeyName', '')
        key_value = tags.get('KeyValue', '')
        
        for server in servers:
            server_tags = server.get('tags', {})
            if key_name in server_tags and server_tags[key_name] == key_value:
                matching_servers.append(server['sourceServerID'])
        
        return matching_servers
        
    except Exception as e:
        print(f"Error validating source servers: {str(e)}")
        raise


def get_drs_source_server_details(account_id: str, region: str, server_ids: List[str]) -> List[Dict]:
    """Get detailed information about DRS source servers"""
    try:
        drs_client = boto3.client('drs', region_name=region)
        
        servers_response = drs_client.describe_source_servers()
        all_servers = servers_response.get('items', [])
        
        # Filter to requested servers
        details = []
        for server in all_servers:
            if server['sourceServerID'] in server_ids:
                details.append({
                    'SourceServerId': server['sourceServerID'],
                    'Hostname': server.get('sourceProperties', {}).get('identificationHints', {}).get('hostname', 'Unknown'),
                    'ReplicationStatus': server.get('dataReplicationInfo', {}).get('dataReplicationState', 'Unknown'),
                    'LastSeenTime': server.get('sourceProperties', {}).get('lastUpdatedDateTime', ''),
                    'LifeCycleState': server.get('lifeCycle', {}).get('state', 'Unknown')
                })
        
        return details
        
    except Exception as e:
        print(f"Error getting server details: {str(e)}")
        return []


def validate_waves(waves: List[Dict]) -> Optional[str]:
    """Validate wave configuration - supports both single and multi-PG formats"""
    try:
        if not waves:
            return "Waves array cannot be empty"
        
        # Check for duplicate wave IDs (if present)
        wave_ids = [w.get('WaveId') for w in waves if w.get('WaveId')]
        if wave_ids and len(wave_ids) != len(set(wave_ids)):
            return "Duplicate WaveId found in waves"
        
        # Check for duplicate execution orders (if present)
        exec_orders = [w.get('ExecutionOrder') for w in waves if w.get('ExecutionOrder') is not None]
        if exec_orders and len(exec_orders) != len(set(exec_orders)):
            return "Duplicate ExecutionOrder found in waves"
        
        # Check for circular dependencies (if present)
        dependency_graph = {}
        for wave in waves:
            wave_id = wave.get('WaveId')
            if wave_id:
                dependencies = [d.get('DependsOnWaveId') for d in wave.get('Dependencies', [])]
                dependency_graph[wave_id] = dependencies
        
        if dependency_graph and has_circular_dependencies(dependency_graph):
            return "Circular dependency detected in wave configuration"
        
        # Validate each wave has required fields
        # NEW: Support both old (single PG) and new (multi-PG) formats
        for wave in waves:
            # Accept both backend (WaveId, WaveName) and frontend (waveNumber, name) formats
            if 'WaveId' not in wave and 'waveNumber' not in wave:
                return "Wave missing required field: WaveId or waveNumber"
            
            if 'WaveName' not in wave and 'name' not in wave:
                return "Wave missing required field: WaveName or name"
            
            # NEW: Accept either protectionGroupId (single) OR protectionGroupIds (multi)
            has_single_pg = 'ProtectionGroupId' in wave or 'protectionGroupId' in wave
            has_multi_pg = 'ProtectionGroupIds' in wave or 'protectionGroupIds' in wave
            
            if not has_single_pg and not has_multi_pg:
                return "Wave missing Protection Group assignment (protectionGroupId or protectionGroupIds required)"
            
            # Validate protectionGroupIds is an array if present
            pg_ids = wave.get('protectionGroupIds') or wave.get('ProtectionGroupIds')
            if pg_ids is not None:
                if not isinstance(pg_ids, list):
                    return f"protectionGroupIds must be an array, got {type(pg_ids)}"
                if len(pg_ids) == 0:
                    return "protectionGroupIds array cannot be empty"
        
        return None  # No errors
        
    except Exception as e:
        return f"Error validating waves: {str(e)}"


def has_circular_dependencies(graph: Dict[str, List[str]]) -> bool:
    """Check for circular dependencies using DFS"""
    visited = set()
    rec_stack = set()
    
    def dfs(node):
        visited.add(node)
        rec_stack.add(node)
        
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                if dfs(neighbor):
                    return True
            elif neighbor in rec_stack:
                return True
        
        rec_stack.remove(node)
        return False
    
    for node in graph:
        if node not in visited:
            if dfs(node):
                return True
    
    return False
