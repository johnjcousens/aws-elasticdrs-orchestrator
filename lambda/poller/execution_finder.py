"""
Execution Finder Lambda
Queries DynamoDB StatusIndex GSI for executions in POLLING status.
Returns list of ExecutionIds for the Execution Poller to process.
"""
import json
import os
import boto3
from typing import List, Dict, Any
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.client('dynamodb')

# Environment variables (with defaults for testing)
EXECUTION_HISTORY_TABLE = os.environ.get('EXECUTION_HISTORY_TABLE', 'test-execution-table')
STATUS_INDEX_NAME = 'StatusIndex'

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for Execution Finder.
    
    Invoked by EventBridge on a schedule (default: 1 minute intervals).
    Queries StatusIndex GSI for executions with Status=POLLING.
    
    Args:
        event: EventBridge scheduled event
        context: Lambda context object
        
    Returns:
        Dict containing list of ExecutionIds found in POLLING status
    """
    try:
        logger.info("Execution Finder Lambda invoked")
        logger.info(f"Querying table: {EXECUTION_HISTORY_TABLE}, index: {STATUS_INDEX_NAME}")
        
        # Query StatusIndex GSI for POLLING executions
        polling_executions = query_polling_executions()
        
        logger.info(f"Found {len(polling_executions)} executions in POLLING status")
        
        # Extract ExecutionIds
        execution_ids = [exec_data['ExecutionId'] for exec_data in polling_executions]
        
        if execution_ids:
            logger.info(f"ExecutionIds to process: {execution_ids}")
        else:
            logger.info("No executions found in POLLING status")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'executionCount': len(execution_ids),
                'executionIds': execution_ids,
                'message': f'Found {len(execution_ids)} executions in POLLING status'
            })
        }
        
    except Exception as e:
        logger.error(f"Error in Execution Finder: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'message': 'Failed to query polling executions'
            })
        }

def query_polling_executions() -> List[Dict[str, Any]]:
    """
    Query DynamoDB StatusIndex GSI for executions with Status=POLLING.
    
    CRITICAL: Status is a reserved keyword in DynamoDB.
    MUST use ExpressionAttributeNames to avoid ValidationException.
    
    Returns:
        List of execution records in POLLING status
    """
    try:
        # CRITICAL: Use expression attribute names for reserved keyword "Status"
        response = dynamodb.query(
            TableName=EXECUTION_HISTORY_TABLE,
            IndexName=STATUS_INDEX_NAME,
            KeyConditionExpression='#status = :status',
            ExpressionAttributeNames={
                '#status': 'Status'  # Required: Status is reserved keyword
            },
            ExpressionAttributeValues={
                ':status': {'S': 'POLLING'}
            }
        )
        
        logger.info(f"DynamoDB query returned {response['Count']} items")
        
        # Parse DynamoDB items to Python dicts
        executions = []
        for item in response.get('Items', []):
            execution = parse_dynamodb_item(item)
            executions.append(execution)
        
        return executions
        
    except Exception as e:
        logger.error(f"Error querying StatusIndex: {str(e)}", exc_info=True)
        raise

def parse_dynamodb_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse DynamoDB item format to Python dict.
    
    Converts DynamoDB's typed format {'S': 'value'} to simple values.
    Handles nested structures (Lists, Maps).
    
    Args:
        item: DynamoDB item in typed format
        
    Returns:
        Parsed Python dictionary
    """
    result = {}
    
    for key, value in item.items():
        if 'S' in value:  # String
            result[key] = value['S']
        elif 'N' in value:  # Number
            result[key] = int(value['N']) if '.' not in value['N'] else float(value['N'])
        elif 'L' in value:  # List
            result[key] = [parse_dynamodb_value(v) for v in value['L']]
        elif 'M' in value:  # Map
            result[key] = parse_dynamodb_item(value['M'])
        elif 'BOOL' in value:  # Boolean
            result[key] = value['BOOL']
        elif 'NULL' in value:  # Null
            result[key] = None
        else:
            result[key] = value
    
    return result

def parse_dynamodb_value(value: Dict[str, Any]) -> Any:
    """
    Parse a single DynamoDB value.
    
    Args:
        value: DynamoDB value in typed format
        
    Returns:
        Parsed Python value
    """
    if 'S' in value:
        return value['S']
    elif 'N' in value:
        return int(value['N']) if '.' not in value['N'] else float(value['N'])
    elif 'L' in value:
        return [parse_dynamodb_value(v) for v in value['L']]
    elif 'M' in value:
        return parse_dynamodb_item(value['M'])
    elif 'BOOL' in value:
        return value['BOOL']
    elif 'NULL' in value:
        return None
    else:
        return value
