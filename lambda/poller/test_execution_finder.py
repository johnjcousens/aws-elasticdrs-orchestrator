"""
Unit tests for Execution Finder Lambda
Tests DynamoDB query logic, parsing, and error handling.
"""
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from execution_finder import (
    lambda_handler,
    query_polling_executions,
    parse_dynamodb_item,
    parse_dynamodb_value
)

# Sample DynamoDB response data
SAMPLE_DYNAMODB_ITEM = {
    'ExecutionId': {'S': 'test-execution-123'},
    'PlanId': {'S': 'plan-456'},
    'Status': {'S': 'POLLING'},
    'StartTime': {'N': '1764345881'},
    'ExecutionType': {'S': 'DRILL'},
    'InitiatedBy': {'S': 'test-user'},
    'Waves': {
        'L': [
            {
                'M': {
                    'WaveName': {'S': 'Database'},
                    'Status': {'S': 'INITIATED'},
                    'Region': {'S': 'us-east-1'}
                }
            }
        ]
    }
}

SAMPLE_QUERY_RESPONSE = {
    'Count': 2,
    'Items': [
        SAMPLE_DYNAMODB_ITEM,
        {
            'ExecutionId': {'S': 'test-execution-456'},
            'PlanId': {'S': 'plan-789'},
            'Status': {'S': 'POLLING'},
            'StartTime': {'N': '1764345900'},
            'ExecutionType': {'S': 'RECOVERY'}
        }
    ]
}

@pytest.fixture
def mock_env(monkeypatch):
    """Set up environment variables for tests."""
    monkeypatch.setenv('EXECUTION_HISTORY_TABLE', 'test-execution-table')

@pytest.fixture
def mock_dynamodb():
    """Mock boto3 DynamoDB client."""
    with patch('execution_finder.dynamodb') as mock:
        yield mock

class TestLambdaHandler:
    """Tests for main Lambda handler function."""
    
    def test_handler_success(self, mock_env, mock_dynamodb):
        """Test successful execution with polling executions found."""
        mock_dynamodb.query.return_value = SAMPLE_QUERY_RESPONSE
        
        event = {}
        context = Mock()
        
        result = lambda_handler(event, context)
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['executionCount'] == 2
        assert len(body['executionIds']) == 2
        assert 'test-execution-123' in body['executionIds']
        assert 'test-execution-456' in body['executionIds']
    
    def test_handler_no_executions(self, mock_env, mock_dynamodb):
        """Test successful execution with no polling executions."""
        mock_dynamodb.query.return_value = {'Count': 0, 'Items': []}
        
        event = {}
        context = Mock()
        
        result = lambda_handler(event, context)
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['executionCount'] == 0
        assert body['executionIds'] == []
    
    def test_handler_error(self, mock_env, mock_dynamodb):
        """Test error handling in Lambda handler."""
        mock_dynamodb.query.side_effect = Exception("DynamoDB error")
        
        event = {}
        context = Mock()
        
        result = lambda_handler(event, context)
        
        assert result['statusCode'] == 500
        body = json.loads(result['body'])
        assert 'error' in body
        assert 'Failed to query polling executions' in body['message']

class TestQueryPollingExecutions:
    """Tests for DynamoDB query function."""
    
    def test_query_success(self, mock_env, mock_dynamodb):
        """Test successful query with attribute name escaping."""
        mock_dynamodb.query.return_value = SAMPLE_QUERY_RESPONSE
        
        executions = query_polling_executions()
        
        # Verify query called with correct parameters
        mock_dynamodb.query.assert_called_once()
        call_args = mock_dynamodb.query.call_args[1]
        
        # CRITICAL: Verify attribute name escaping for reserved keyword
        assert call_args['KeyConditionExpression'] == '#status = :status'
        assert call_args['ExpressionAttributeNames'] == {'#status': 'Status'}
        assert call_args['ExpressionAttributeValues'] == {':status': {'S': 'POLLING'}}
        assert call_args['IndexName'] == 'StatusIndex'
        
        # Verify results parsed correctly
        assert len(executions) == 2
        assert executions[0]['ExecutionId'] == 'test-execution-123'
        assert executions[0]['Status'] == 'POLLING'
    
    def test_query_error(self, mock_env, mock_dynamodb):
        """Test error handling in query function."""
        mock_dynamodb.query.side_effect = Exception("Query failed")
        
        with pytest.raises(Exception) as exc_info:
            query_polling_executions()
        
        assert "Query failed" in str(exc_info.value)

class TestParseDynamoDBItem:
    """Tests for DynamoDB item parsing."""
    
    def test_parse_string(self):
        """Test parsing string attribute."""
        item = {'Name': {'S': 'test-name'}}
        result = parse_dynamodb_item(item)
        assert result['Name'] == 'test-name'
    
    def test_parse_number_int(self):
        """Test parsing integer number attribute."""
        item = {'Count': {'N': '123'}}
        result = parse_dynamodb_item(item)
        assert result['Count'] == 123
        assert isinstance(result['Count'], int)
    
    def test_parse_number_float(self):
        """Test parsing float number attribute."""
        item = {'Price': {'N': '123.45'}}
        result = parse_dynamodb_item(item)
        assert result['Price'] == 123.45
        assert isinstance(result['Price'], float)
    
    def test_parse_boolean(self):
        """Test parsing boolean attribute."""
        item = {'Active': {'BOOL': True}}
        result = parse_dynamodb_item(item)
        assert result['Active'] is True
    
    def test_parse_null(self):
        """Test parsing null attribute."""
        item = {'Error': {'NULL': True}}
        result = parse_dynamodb_item(item)
        assert result['Error'] is None
    
    def test_parse_list(self):
        """Test parsing list attribute."""
        item = {
            'Tags': {
                'L': [
                    {'S': 'tag1'},
                    {'S': 'tag2'}
                ]
            }
        }
        result = parse_dynamodb_item(item)
        assert result['Tags'] == ['tag1', 'tag2']
    
    def test_parse_map(self):
        """Test parsing map (nested object) attribute."""
        item = {
            'Wave': {
                'M': {
                    'WaveName': {'S': 'Database'},
                    'Status': {'S': 'INITIATED'}
                }
            }
        }
        result = parse_dynamodb_item(item)
        assert result['Wave']['WaveName'] == 'Database'
        assert result['Wave']['Status'] == 'INITIATED'
    
    def test_parse_complex_nested(self):
        """Test parsing complex nested structure."""
        result = parse_dynamodb_item(SAMPLE_DYNAMODB_ITEM)
        
        assert result['ExecutionId'] == 'test-execution-123'
        assert result['Status'] == 'POLLING'
        assert result['StartTime'] == 1764345881
        assert len(result['Waves']) == 1
        assert result['Waves'][0]['WaveName'] == 'Database'

class TestParseDynamoDBValue:
    """Tests for individual DynamoDB value parsing."""
    
    def test_parse_string_value(self):
        """Test parsing string value."""
        value = {'S': 'test-string'}
        result = parse_dynamodb_value(value)
        assert result == 'test-string'
    
    def test_parse_number_value(self):
        """Test parsing number value."""
        value = {'N': '42'}
        result = parse_dynamodb_value(value)
        assert result == 42
    
    def test_parse_list_value(self):
        """Test parsing list value."""
        value = {
            'L': [
                {'S': 'item1'},
                {'N': '123'}
            ]
        }
        result = parse_dynamodb_value(value)
        assert result == ['item1', 123]
    
    def test_parse_map_value(self):
        """Test parsing map value."""
        value = {
            'M': {
                'Key': {'S': 'value'}
            }
        }
        result = parse_dynamodb_value(value)
        assert result['Key'] == 'value'

class TestIntegration:
    """Integration tests for full workflow."""
    
    def test_full_workflow(self, mock_env, mock_dynamodb):
        """Test complete workflow from Lambda invocation to response."""
        # Setup mock response with real-world data structure
        mock_dynamodb.query.return_value = {
            'Count': 1,
            'Items': [SAMPLE_DYNAMODB_ITEM]
        }
        
        # Invoke Lambda handler
        event = {'source': 'aws.events'}  # EventBridge event
        context = Mock()
        context.function_name = 'execution-finder'
        context.request_id = 'test-request-123'
        
        result = lambda_handler(event, context)
        
        # Verify successful response
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        
        # Verify correct execution IDs returned
        assert body['executionCount'] == 1
        assert body['executionIds'] == ['test-execution-123']
        assert 'Found 1 executions' in body['message']

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
