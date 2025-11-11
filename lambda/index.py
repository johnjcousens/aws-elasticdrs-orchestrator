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
    """Create a new Protection Group"""
    try:
        # Validate required fields
        required_fields = ['GroupName', 'Description', 'Tags', 'AccountId', 'Region', 'Owner']
        for field in required_fields:
            if field not in body:
                return response(400, {'error': f'Missing required field: {field}'})
        
        # Generate UUID for GroupId
        group_id = str(uuid.uuid4())
        
        # Validate source servers exist with specified tags
        source_server_ids = validate_and_get_source_servers(
            body['AccountId'],
            body['Region'],
            body['Tags']
        )
        
        if not source_server_ids:
            return response(400, {
                'error': 'No source servers found with specified tags',
                'tags': body['Tags']
            })
        
        # Create Protection Group item
        timestamp = int(time.time())
        item = {
            'GroupId': group_id,
            'GroupName': body['GroupName'],
            'Description': body['Description'],
            'SourceServerIds': source_server_ids,
            'Tags': body['Tags'],
            'AccountId': body['AccountId'],
            'Region': body['Region'],
            'Owner': body['Owner'],
            'CreatedDate': timestamp,
            'LastModifiedDate': timestamp
        }
        
        # Store in DynamoDB
        protection_groups_table.put_item(Item=item)
        
        print(f"Created Protection Group: {group_id}")
        return response(201, item)
        
    except Exception as e:
        print(f"Error creating Protection Group: {str(e)}")
        return response(500, {'error': str(e)})


def get_protection_groups() -> Dict:
    """List all Protection Groups"""
    try:
        result = protection_groups_table.scan()
        groups = result.get('Items', [])
        
        # Enrich with current DRS source server status
        for group in groups:
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
        
        return response(200, {'groups': groups, 'count': len(groups)})
        
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
        
        return response(200, group)
        
    except Exception as e:
        print(f"Error getting Protection Group: {str(e)}")
        return response(500, {'error': str(e)})


def update_protection_group(group_id: str, body: Dict) -> Dict:
    """Update an existing Protection Group"""
    try:
        # Check if group exists
        result = protection_groups_table.get_item(Key={'GroupId': group_id})
        if 'Item' not in result:
            return response(404, {'error': 'Protection Group not found'})
        
        existing_group = result['Item']
        
        # Update allowed fields
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
        
        if 'Tags' in body:
            # Re-validate source servers with new tags
            source_server_ids = validate_and_get_source_servers(
                existing_group['AccountId'],
                existing_group['Region'],
                body['Tags']
            )
            update_expression += ", Tags = :tags, SourceServerIds = :servers"
            expression_values[':tags'] = body['Tags']
            expression_values[':servers'] = source_server_ids
        
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
        
        # Add wave counts
        for plan in plans:
            plan['WaveCount'] = len(plan.get('Waves', []))
        
        return response(200, {'plans': plans, 'count': len(plans)})
        
    except Exception as e:
        print(f"Error listing Recovery Plans: {str(e)}")
        return response(500, {'error': str(e)})


def get_recovery_plan(plan_id: str) -> Dict:
    """Get a single Recovery Plan by ID"""
    try:
        result = recovery_plans_table.get_item(Key={'PlanId': plan_id})
        
        if 'Item' not in result:
            return response(404, {'error': 'Recovery Plan not found'})
        
        return response(200, result['Item'])
        
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
        # Check for active executions
        executions_result = execution_history_table.query(
            IndexName='PlanIdIndex',
            KeyConditionExpression=Key('PlanId').eq(plan_id),
            FilterExpression=Attr('Status').eq('RUNNING')
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
# DRS Source Servers Handler
# ============================================================================

def handle_drs_source_servers(query_params: Dict) -> Dict:
    """List DRS source servers"""
    try:
        account_id = query_params.get('accountId')
        region = query_params.get('region')
        
        if not account_id or not region:
            return response(400, {'error': 'Missing accountId or region parameter'})
        
        # For now, use current account credentials
        # In production, would assume cross-account role
        drs_client = boto3.client('drs', region_name=region)
        
        # Get source servers
        servers_response = drs_client.describe_source_servers()
        servers = servers_response.get('items', [])
        
        # Format response
        formatted_servers = []
        for server in servers:
            formatted_servers.append({
                'SourceServerId': server.get('sourceServerID'),
                'Hostname': server.get('sourceProperties', {}).get('identificationHints', {}).get('hostname', 'Unknown'),
                'ReplicationStatus': server.get('dataReplicationInfo', {}).get('dataReplicationState', 'Unknown'),
                'LastSeenTime': server.get('sourceProperties', {}).get('lastUpdatedDateTime', ''),
                'Tags': server.get('tags', {})
            })
        
        return response(200, {
            'servers': formatted_servers,
            'count': len(formatted_servers)
        })
        
    except Exception as e:
        print(f"Error listing DRS source servers: {str(e)}")
        return response(500, {'error': str(e)})


# ============================================================================
# Helper Functions
# ============================================================================

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
    """Validate wave configuration"""
    try:
        if not waves:
            return "Waves array cannot be empty"
        
        # Check for duplicate wave IDs
        wave_ids = [w.get('WaveId') for w in waves]
        if len(wave_ids) != len(set(wave_ids)):
            return "Duplicate WaveId found in waves"
        
        # Check for duplicate execution orders
        exec_orders = [w.get('ExecutionOrder') for w in waves]
        if len(exec_orders) != len(set(exec_orders)):
            return "Duplicate ExecutionOrder found in waves"
        
        # Check for circular dependencies
        dependency_graph = {}
        for wave in waves:
            wave_id = wave.get('WaveId')
            dependencies = [d.get('DependsOnWaveId') for d in wave.get('Dependencies', [])]
            dependency_graph[wave_id] = dependencies
        
        if has_circular_dependencies(dependency_graph):
            return "Circular dependency detected in wave configuration"
        
        # Validate each wave has required fields
        for wave in waves:
            required_fields = ['WaveId', 'WaveName', 'ExecutionOrder', 'ProtectionGroupId']
            for field in required_fields:
                if field not in wave:
                    return f"Wave missing required field: {field}"
        
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
