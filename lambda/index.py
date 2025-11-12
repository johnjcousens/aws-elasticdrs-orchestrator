"""
AWS DRS Orchestration - API Handler Lambda
Handles REST API requests for Protection Groups, Recovery Plans, and Executions
"""

import json
import os
import uuid
import time
import boto3
from boto3.dynamodb.conditions import Key, Attr
from decimal import Decimal
from typing import Dict, Any, List, Optional

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
stepfunctions = boto3.client('stepfunctions')
drs = boto3.client('drs')

# Environment variables
PROTECTION_GROUPS_TABLE = os.environ['PROTECTION_GROUPS_TABLE']
RECOVERY_PLANS_TABLE = os.environ['RECOVERY_PLANS_TABLE']
EXECUTION_HISTORY_TABLE = os.environ['EXECUTION_HISTORY_TABLE']
STATE_MACHINE_ARN = os.environ.get('STATE_MACHINE_ARN', '')

# DynamoDB tables
protection_groups_table = dynamodb.Table(PROTECTION_GROUPS_TABLE)
recovery_plans_table = dynamodb.Table(RECOVERY_PLANS_TABLE)
execution_history_table = dynamodb.Table(EXECUTION_HISTORY_TABLE)


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


def lambda_handler(event: Dict, context: Any) -> Dict:
    """Main Lambda handler - routes requests to appropriate functions"""
    print(f"Received event: {json.dumps(event)}")
    
    try:
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
        elif path.startswith('/recovery-plans'):
            return handle_recovery_plans(http_method, path_parameters, body)
        elif path.startswith('/executions'):
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
        
        # If updating server list, validate assignments
        if 'sourceServerIds' in body:
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
    """Delete a Protection Group"""
    try:
        # Check if group is referenced in any Recovery Plans
        plans_result = recovery_plans_table.scan(
            FilterExpression=Attr('Waves').contains({'ProtectionGroupId': group_id})
        )
        
        if plans_result.get('Items'):
            plan_names = [p['PlanName'] for p in plans_result['Items']]
            return response(400, {
                'error': 'Protection Group is referenced in active Recovery Plans',
                'plans': plan_names
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
        required_fields = ['PlanName', 'Description', 'AccountId', 'Region', 'Owner', 'RPO', 'RTO']
        for field in required_fields:
            if field not in body:
                return response(400, {'error': f'Missing required field: {field}'})
        
        # Generate UUID for PlanId
        plan_id = str(uuid.uuid4())
        
        # Create Recovery Plan item
        timestamp = int(time.time())
        item = {
            'PlanId': plan_id,
            'PlanName': body['PlanName'],
            'Description': body['Description'],
            'AccountId': body['AccountId'],
            'Region': body['Region'],
            'Owner': body['Owner'],
            'RPO': body['RPO'],
            'RTO': body['RTO'],
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
    """List all Recovery Plans"""
    try:
        result = recovery_plans_table.scan()
        plans = result.get('Items', [])
        
        # Transform to camelCase for frontend
        camelcase_plans = []
        for plan in plans:
            # Add wave count before transformation
            plan['WaveCount'] = len(plan.get('Waves', []))
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
    """Update an existing Recovery Plan"""
    try:
        # Check if plan exists
        result = recovery_plans_table.get_item(Key={'PlanId': plan_id})
        if 'Item' not in result:
            return response(404, {'error': 'Recovery Plan not found'})
        
        # Validate waves if provided
        if 'Waves' in body:
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
    """Delete a Recovery Plan"""
    try:
        # Check for active executions using scan (doesn't require GSI)
        executions_result = execution_history_table.scan(
            FilterExpression=Attr('PlanId').eq(plan_id) & Attr('Status').eq('RUNNING')
        )
        
        if executions_result.get('Items'):
            return response(400, {
                'error': 'Cannot delete Recovery Plan with active executions',
                'activeExecutions': len(executions_result['Items'])
            })
        
        # Delete the plan
        recovery_plans_table.delete_item(Key={'PlanId': plan_id})
        
        print(f"Deleted Recovery Plan: {plan_id}")
        return response(200, {'message': 'Recovery Plan deleted successfully'})
        
    except Exception as e:
        print(f"Error deleting Recovery Plan: {str(e)}")
        return response(500, {'error': str(e)})


# ============================================================================
# Execution Handlers
# ============================================================================

def handle_executions(method: str, path_params: Dict, query_params: Dict, body: Dict) -> Dict:
    """Route Execution requests"""
    execution_id = path_params.get('executionId')
    path = path_params.get('path', '')
    
    # Handle action-specific routes
    if execution_id and 'cancel' in path:
        return cancel_execution(execution_id)
    elif execution_id and 'pause' in path:
        return pause_execution(execution_id)
    elif execution_id and 'resume' in path:
        return resume_execution(execution_id)
    elif method == 'POST' and not execution_id:
        return execute_recovery_plan(body)
    elif method == 'GET' and execution_id:
        return get_execution_details(execution_id)
    elif method == 'GET':
        # List all executions with optional pagination
        return list_executions(query_params)
    else:
        return response(405, {'error': 'Method Not Allowed'})


def execute_recovery_plan(body: Dict) -> Dict:
    """Execute a Recovery Plan"""
    try:
        # Validate required fields
        required_fields = ['PlanId', 'ExecutionType', 'InitiatedBy']
        for field in required_fields:
            if field not in body:
                return response(400, {'error': f'Missing required field: {field}'})
        
        plan_id = body['PlanId']
        execution_type = body['ExecutionType']
        
        # Validate execution type
        if execution_type not in ['DRILL', 'RECOVERY', 'FAILBACK']:
            return response(400, {'error': 'Invalid ExecutionType'})
        
        # Get Recovery Plan
        plan_result = recovery_plans_table.get_item(Key={'PlanId': plan_id})
        if 'Item' not in plan_result:
            return response(404, {'error': 'Recovery Plan not found'})
        
        plan = plan_result['Item']
        
        # Validate plan has waves
        if not plan.get('Waves'):
            return response(400, {'error': 'Recovery Plan has no waves configured'})
        
        # Start Step Functions execution
        execution_input = {
            'ExecutionType': execution_type,
            'PlanId': plan_id,
            'InitiatedBy': body['InitiatedBy'],
            'TopicArn': body.get('TopicArn', ''),
            'DryRun': body.get('DryRun', False)
        }
        
        sf_response = stepfunctions.start_execution(
            stateMachineArn=STATE_MACHINE_ARN,
            input=json.dumps(execution_input)
        )
        
        execution_arn = sf_response['executionArn']
        
        # Create initial execution history record
        timestamp = int(time.time())
        history_item = {
            'ExecutionId': execution_arn,
            'PlanId': plan_id,
            'ExecutionType': execution_type,
            'Status': 'RUNNING',
            'StartTime': timestamp,
            'InitiatedBy': body['InitiatedBy'],
            'TopicArn': body.get('TopicArn', ''),
            'WaveResults': []
        }
        
        execution_history_table.put_item(Item=history_item)
        
        # Update plan's LastExecutedDate
        recovery_plans_table.update_item(
            Key={'PlanId': plan_id},
            UpdateExpression='SET LastExecutedDate = :timestamp',
            ExpressionAttributeValues={':timestamp': timestamp}
        )
        
        print(f"Started execution: {execution_arn}")
        return response(202, {
            'executionArn': execution_arn,
            'executionId': execution_arn,
            'status': 'RUNNING',
            'message': 'Execution started successfully'
        })
        
    except Exception as e:
        print(f"Error executing Recovery Plan: {str(e)}")
        return response(500, {'error': str(e)})


def get_execution_status(execution_id: str) -> Dict:
    """Get current execution status"""
    try:
        # Get from DynamoDB
        result = execution_history_table.get_item(Key={'ExecutionId': execution_id})
        
        if 'Item' not in result:
            return response(404, {'error': 'Execution not found'})
        
        execution = result['Item']
        
        # Get current status from Step Functions if still running
        if execution['Status'] == 'RUNNING':
            try:
                sf_response = stepfunctions.describe_execution(
                    executionArn=execution_id
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
        
        # Enrich with recovery plan names
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
        
        # Build response with pagination
        response_data = {
            'items': executions,
            'count': len(executions)
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


def get_execution_details(execution_id: str) -> Dict:
    """Get detailed information about a specific execution"""
    try:
        # Get from DynamoDB
        result = execution_history_table.get_item(Key={'ExecutionId': execution_id})
        
        if 'Item' not in result:
            return response(404, {'error': 'Execution not found'})
        
        execution = result['Item']
        
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
        
        # Get current status from Step Functions if still running
        if execution.get('Status') == 'RUNNING':
            try:
                sf_response = stepfunctions.describe_execution(
                    executionArn=execution_id
                )
                execution['StepFunctionsStatus'] = sf_response['status']
                
                # Update DynamoDB if Step Functions shows completion
                if sf_response['status'] in ['SUCCEEDED', 'FAILED', 'TIMED_OUT', 'ABORTED']:
                    new_status = 'COMPLETED' if sf_response['status'] == 'SUCCEEDED' else 'FAILED'
                    execution_history_table.update_item(
                        Key={'ExecutionId': execution_id},
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
        
        return response(200, execution)
        
    except Exception as e:
        print(f"Error getting execution details: {str(e)}")
        return response(500, {'error': str(e)})


def cancel_execution(execution_id: str) -> Dict:
    """Cancel a running execution"""
    try:
        # Check if execution exists
        result = execution_history_table.get_item(Key={'ExecutionId': execution_id})
        
        if 'Item' not in result:
            return response(404, {'error': 'Execution not found'})
        
        execution = result['Item']
        
        # Check if execution is still running
        if execution.get('Status') not in ['RUNNING', 'PAUSED']:
            return response(400, {
                'error': 'Execution is not running',
                'currentStatus': execution.get('Status')
            })
        
        # Stop Step Functions execution
        try:
            stepfunctions.stop_execution(
                executionArn=execution_id,
                error='UserCancelled',
                cause='Execution cancelled by user'
            )
            print(f"Stopped Step Functions execution: {execution_id}")
        except Exception as e:
            print(f"Error stopping Step Functions execution: {str(e)}")
            # Continue to update DynamoDB even if Step Functions call fails
        
        # Update DynamoDB status
        timestamp = int(time.time())
        execution_history_table.update_item(
            Key={'ExecutionId': execution_id},
            UpdateExpression='SET #status = :status, EndTime = :endtime',
            ExpressionAttributeNames={'#status': 'Status'},
            ExpressionAttributeValues={
                ':status': 'CANCELLED',
                ':endtime': timestamp
            }
        )
        
        print(f"Cancelled execution: {execution_id}")
        return response(200, {
            'executionId': execution_id,
            'status': 'CANCELLED',
            'message': 'Execution cancelled successfully'
        })
        
    except Exception as e:
        print(f"Error cancelling execution: {str(e)}")
        return response(500, {'error': str(e)})


def pause_execution(execution_id: str) -> Dict:
    """Pause a running execution (Note: Step Functions doesn't support native pause)"""
    try:
        # Check if execution exists
        result = execution_history_table.get_item(Key={'ExecutionId': execution_id})
        
        if 'Item' not in result:
            return response(404, {'error': 'Execution not found'})
        
        execution = result['Item']
        
        # Check if execution is running
        if execution.get('Status') != 'RUNNING':
            return response(400, {
                'error': 'Execution is not running',
                'currentStatus': execution.get('Status')
            })
        
        # Note: AWS Step Functions doesn't support pausing executions natively
        # This is a placeholder for future implementation with custom logic
        # For now, we'll mark it as paused in DynamoDB but the Step Functions execution continues
        
        execution_history_table.update_item(
            Key={'ExecutionId': execution_id},
            UpdateExpression='SET #status = :status',
            ExpressionAttributeNames={'#status': 'Status'},
            ExpressionAttributeValues={':status': 'PAUSED'}
        )
        
        print(f"Marked execution as paused: {execution_id}")
        return response(200, {
            'executionId': execution_id,
            'status': 'PAUSED',
            'message': 'Execution marked as paused (Note: Step Functions continues running)',
            'warning': 'Step Functions does not support native pause - this is a logical state only'
        })
        
    except Exception as e:
        print(f"Error pausing execution: {str(e)}")
        return response(500, {'error': str(e)})


def resume_execution(execution_id: str) -> Dict:
    """Resume a paused execution (Note: Step Functions doesn't support native resume)"""
    try:
        # Check if execution exists
        result = execution_history_table.get_item(Key={'ExecutionId': execution_id})
        
        if 'Item' not in result:
            return response(404, {'error': 'Execution not found'})
        
        execution = result['Item']
        
        # Check if execution is paused
        if execution.get('Status') != 'PAUSED':
            return response(400, {
                'error': 'Execution is not paused',
                'currentStatus': execution.get('Status')
            })
        
        # Update status back to RUNNING
        execution_history_table.update_item(
            Key={'ExecutionId': execution_id},
            UpdateExpression='SET #status = :status',
            ExpressionAttributeNames={'#status': 'Status'},
            ExpressionAttributeValues={':status': 'RUNNING'}
        )
        
        print(f"Resumed execution: {execution_id}")
        return response(200, {
            'executionId': execution_id,
            'status': 'RUNNING',
            'message': 'Execution resumed successfully'
        })
        
    except Exception as e:
        print(f"Error resuming execution: {str(e)}")
        return response(500, {'error': str(e)})


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
                'message': f'DRS is not initialized in {region}. Please initialize DRS before creating Protection Groups.',
                'region': region,
                'initialized': False
            })
        except Exception as e:
            print(f"Error querying DRS: {str(e)}")
            # Check if it's an uninitialized error by message
            if 'UninitializedAccountException' in str(e) or 'not initialized' in str(e).lower():
                return response(400, {
                    'error': 'DRS_NOT_INITIALIZED',
                    'message': f'DRS is not initialized in {region}. Please initialize DRS before creating Protection Groups.',
                    'region': region,
                    'initialized': False
                })
            raise
        
        # 2. Build server list from DRS response
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
                'assignedToProtectionGroup': None,  # Will be populated below
                'selectable': True  # Will be updated below
            })
        
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


# ============================================================================
# Helper Functions
# ============================================================================

def transform_pg_to_camelcase(pg: Dict) -> Dict:
    """Transform Protection Group from DynamoDB PascalCase to frontend camelCase"""
    return {
        'protectionGroupId': pg.get('GroupId'),
        'name': pg.get('GroupName'),
        'description': pg.get('Description', ''),
        'region': pg.get('Region'),
        'sourceServerIds': pg.get('SourceServerIds', []),
        'accountId': pg.get('AccountId', ''),
        'owner': pg.get('Owner', ''),
        'createdAt': pg.get('CreatedDate'),
        'updatedAt': pg.get('LastModifiedDate'),
        'serverDetails': pg.get('ServerDetails', [])
    }


def transform_rp_to_camelcase(rp: Dict) -> Dict:
    """Transform Recovery Plan from DynamoDB PascalCase to frontend camelCase"""
    
    # Transform waves array from backend PascalCase to frontend camelCase
    waves = []
    for idx, wave in enumerate(rp.get('Waves', [])):
        # Extract dependency wave numbers from WaveId format (e.g., "wave-0" -> 0)
        depends_on_waves = []
        for dep in wave.get('Dependencies', []):
            wave_id = dep.get('DependsOnWaveId', '')
            if wave_id and '-' in wave_id:
                try:
                    wave_num = int(wave_id.split('-')[-1])
                    depends_on_waves.append(wave_num)
                except (ValueError, IndexError):
                    pass
        
        # ROBUST: Extract ServerIds with multiple fallback strategies
        server_ids = wave.get('ServerIds', [])
        
        # Handle boto3 deserialization - ensure we have a list
        if not isinstance(server_ids, list):
            print(f"WARNING: ServerIds is not a list, got type {type(server_ids)}: {server_ids}")
            server_ids = []
        
        # DEFENSIVE: Log wave transformation for debugging
        print(f"Transforming wave {idx}: name={wave.get('WaveName')}, serverIds count={len(server_ids)}")
        
        waves.append({
            'waveNumber': idx,
            'name': wave.get('WaveName', ''),
            'description': wave.get('WaveDescription', ''),
            'serverIds': server_ids,  # Now guaranteed to be a list
            'executionType': wave.get('ExecutionType', 'sequential'),
            'dependsOnWaves': depends_on_waves,
            'protectionGroupId': wave.get('ProtectionGroupId'),  # camelCase for frontend
            'protectionGroupIds': [wave.get('ProtectionGroupId')] if wave.get('ProtectionGroupId') else []  # Array format
        })
    
    return {
        'id': rp.get('PlanId'),
        'name': rp.get('PlanName'),
        'description': rp.get('Description', ''),
        'accountId': rp.get('AccountId'),
        'region': rp.get('Region'),
        'owner': rp.get('Owner'),
        'rpo': rp.get('RPO'),
        'rto': rp.get('RTO'),
        'waves': waves,  # Now properly transformed
        'createdAt': rp.get('CreatedDate'),
        'updatedAt': rp.get('LastModifiedDate'),
        'lastExecutedAt': rp.get('LastExecutedDate'),
        'waveCount': len(waves)
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
