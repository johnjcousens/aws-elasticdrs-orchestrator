"""
Execution Registry Lambda
Creates and updates execution records in DynamoDB for all invocation sources.
Enables dual-mode orchestration where executions from UI, CLI, EventBridge, 
SSM, and Step Functions all appear in the frontend.
"""

import json
import os
import uuid
import time
import boto3
from decimal import Decimal
from typing import Dict, Any, Optional

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')

# Environment variables
EXECUTION_HISTORY_TABLE = os.environ.get('EXECUTION_HISTORY_TABLE', 'execution-history')

# Get table reference
execution_table = dynamodb.Table(EXECUTION_HISTORY_TABLE)


class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder for DynamoDB Decimal types"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super(DecimalEncoder, self).default(obj)


def lambda_handler(event: Dict, context: Any) -> Dict:
    """
    Main handler - routes to appropriate action.
    
    Actions:
    - register: Create new execution record
    - update: Update execution status/waves
    - complete: Mark execution as complete
    - get: Get execution by ID
    """
    print(f"Execution Registry received: {json.dumps(event, cls=DecimalEncoder)}")
    
    action = event.get('action', 'register')
    
    try:
        if action == 'register':
            return register_execution(event)
        elif action == 'update':
            return update_execution(event)
        elif action == 'complete':
            return complete_execution(event)
        elif action == 'get':
            return get_execution(event)
        else:
            raise ValueError(f"Unknown action: {action}")
    except Exception as e:
        print(f"Error in execution registry: {str(e)}")
        raise


def register_execution(event: Dict) -> Dict:
    """
    Create new execution record.
    
    Supports both:
    - Plan-based: Traditional UI flow with PlanId
    - Tag-based: Automation flow with tags for server selection
    """
    execution_id = str(uuid.uuid4())
    timestamp = int(time.time())
    
    # Determine selection mode
    selection_mode = 'TAGS' if event.get('tags') else 'PLAN'
    
    # Get invocation source and details
    invocation_source = event.get('invocationSource', 'API')
    invocation_details = event.get('invocationDetails', {})
    
    # Build human-readable InitiatedBy string
    initiated_by = build_initiated_by(invocation_source, invocation_details)
    
    # Determine execution type
    options = event.get('options', {})
    is_drill = options.get('isDrill', True)
    execution_type = 'DRILL' if is_drill else 'RECOVERY'
    
    # Build execution record
    item = {
        'ExecutionId': execution_id,
        'PlanId': event.get('planId'),  # null for tag-based
        'ExecutionType': execution_type,
        'Status': 'PENDING',
        'StartTime': timestamp,
        
        # Dual-mode fields
        'InvocationSource': invocation_source,
        'InvocationDetails': invocation_details,
        'SelectionMode': selection_mode,
        'Tags': event.get('tags', {}),
        
        # Display fields
        'InitiatedBy': initiated_by,
        'Waves': [],
        'TotalWaves': 0,
        'TotalServers': 0,
        
        # Options
        'Options': options
    }
    
    # Store in DynamoDB
    execution_table.put_item(Item=item)
    
    print(f"Registered execution {execution_id} from {invocation_source}")
    
    return {
        'executionId': execution_id,
        'status': 'PENDING',
        'invocationSource': invocation_source,
        'selectionMode': selection_mode,
        'initiatedBy': initiated_by
    }


def build_initiated_by(source: str, details: Dict) -> str:
    """Build human-readable InitiatedBy string for display"""
    if source == 'UI':
        return details.get('userEmail', 'UI User')
    elif source == 'CLI':
        user = details.get('iamUser') or details.get('correlationId', 'unknown')
        return f"cli:{user}"
    elif source == 'EVENTBRIDGE':
        rule = details.get('scheduleRuleName', 'unknown')
        return f"schedule:{rule}"
    elif source == 'SSM':
        doc = details.get('ssmDocumentName', 'unknown')
        return f"ssm:{doc}"
    elif source == 'STEPFUNCTIONS':
        parent = details.get('parentExecutionId', 'unknown')
        return f"stepfunctions:{parent[:8]}..." if len(parent) > 8 else f"stepfunctions:{parent}"
    else:
        correlation = details.get('correlationId', 'unknown')
        return f"api:{correlation}"


def update_execution(event: Dict) -> Dict:
    """Update execution status, waves, or other fields"""
    execution_id = event['executionId']
    
    update_parts = ['LastUpdated = :updated']
    expr_names = {}
    expr_values = {':updated': int(time.time())}
    
    # Status update
    if 'status' in event:
        update_parts.append('#status = :status')
        expr_names['#status'] = 'Status'
        expr_values[':status'] = event['status']
    
    # Waves update
    if 'waves' in event:
        update_parts.append('Waves = :waves')
        expr_values[':waves'] = event['waves']
    
    # Total waves
    if 'totalWaves' in event:
        update_parts.append('TotalWaves = :totalWaves')
        expr_values[':totalWaves'] = event['totalWaves']
    
    # Total servers
    if 'totalServers' in event:
        update_parts.append('TotalServers = :totalServers')
        expr_values[':totalServers'] = event['totalServers']
    
    # Current wave
    if 'currentWave' in event:
        update_parts.append('CurrentWave = :currentWave')
        expr_values[':currentWave'] = event['currentWave']
    
    # Error message
    if 'errorMessage' in event:
        update_parts.append('ErrorMessage = :errorMessage')
        expr_values[':errorMessage'] = event['errorMessage']
    
    update_expr = 'SET ' + ', '.join(update_parts)
    
    update_kwargs = {
        'Key': {'ExecutionId': execution_id},
        'UpdateExpression': update_expr,
        'ExpressionAttributeValues': expr_values
    }
    
    if expr_names:
        update_kwargs['ExpressionAttributeNames'] = expr_names
    
    execution_table.update_item(**update_kwargs)
    
    print(f"Updated execution {execution_id}: {event.get('status', 'no status change')}")
    
    return {
        'executionId': execution_id,
        'status': event.get('status', 'UPDATED')
    }


def complete_execution(event: Dict) -> Dict:
    """Mark execution as complete with final result"""
    execution_id = event['executionId']
    result = event.get('result', {})
    
    # Normalize status
    status = result.get('status', 'COMPLETED').upper()
    if status == 'SUCCESS':
        status = 'COMPLETED'
    elif status == 'PARTIAL':
        status = 'PARTIAL'
    elif status in ['FAILED', 'ERROR']:
        status = 'FAILED'
    elif status == 'TIMEOUT':
        status = 'TIMEOUT'
    
    timestamp = int(time.time())
    
    update_expr = 'SET #status = :status, EndTime = :endTime, #result = :result, LastUpdated = :updated'
    expr_names = {
        '#status': 'Status',
        '#result': 'Result'
    }
    expr_values = {
        ':status': status,
        ':endTime': timestamp,
        ':result': result,
        ':updated': timestamp
    }
    
    # Update summary fields if provided
    summary = result.get('summary', {})
    if summary:
        if 'totalServers' in summary:
            update_expr += ', TotalServers = :totalServers'
            expr_values[':totalServers'] = summary['totalServers']
        if 'succeeded' in summary:
            update_expr += ', SucceededServers = :succeeded'
            expr_values[':succeeded'] = summary['succeeded']
        if 'failed' in summary:
            update_expr += ', FailedServers = :failed'
            expr_values[':failed'] = summary['failed']
    
    execution_table.update_item(
        Key={'ExecutionId': execution_id},
        UpdateExpression=update_expr,
        ExpressionAttributeNames=expr_names,
        ExpressionAttributeValues=expr_values
    )
    
    print(f"Completed execution {execution_id} with status {status}")
    
    return {
        'executionId': execution_id,
        'status': status,
        'endTime': timestamp
    }


def get_execution(event: Dict) -> Dict:
    """Get execution by ID"""
    execution_id = event['executionId']
    
    result = execution_table.get_item(Key={'ExecutionId': execution_id})
    item = result.get('Item')
    
    if not item:
        raise ValueError(f"Execution not found: {execution_id}")
    
    return item
