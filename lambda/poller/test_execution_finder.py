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

class TestShouldPollNow:
    """Tests for adaptive polling interval logic."""
    
    def test_should_poll_first_time(self):
        """Test polling when LastPolledTime is 0 (first poll)."""
        from execution_finder import should_poll_now
        
        execution = {
            'ExecutionId': 'test-123',
            'LastPolledTime': 0,
            'Waves': []
        }
        
        # Should always poll on first time (LastPolledTime=0)
        assert should_poll_now(execution) is True
    
    def test_should_poll_pending_phase_interval(self):
        """Test 45s interval for PENDING phase."""
        from execution_finder import should_poll_now
        from datetime import datetime, timezone
        
        # Set last poll to 46 seconds ago (> 45s threshold)
        last_poll = datetime.now(timezone.utc).timestamp() - 46
        
        execution = {
            'ExecutionId': 'test-123',
            'LastPolledTime': last_poll,
            'Waves': [{
                'Servers': [{'Status': 'NOT_STARTED'}]
            }]
        }
        
        assert should_poll_now(execution) is True
    
    def test_should_not_poll_pending_phase_too_soon(self):
        """Test skipping poll if < 45s for PENDING phase."""
        from execution_finder import should_poll_now
        from datetime import datetime, timezone
        
        # Set last poll to 40 seconds ago (< 45s threshold)
        last_poll = datetime.now(timezone.utc).timestamp() - 40
        
        execution = {
            'ExecutionId': 'test-123',
            'LastPolledTime': last_poll,
            'Waves': [{
                'Servers': [{'Status': 'NOT_STARTED'}]
            }]
        }
        
        assert should_poll_now(execution) is False
    
    def test_should_poll_started_phase_interval(self):
        """Test 15s interval for STARTED phase (critical)."""
        from execution_finder import should_poll_now
        from datetime import datetime, timezone
        
        # Set last poll to 16 seconds ago (> 15s threshold)
        last_poll = datetime.now(timezone.utc).timestamp() - 16
        
        execution = {
            'ExecutionId': 'test-123',
            'LastPolledTime': last_poll,
            'Waves': [{
                'Servers': [{'Status': 'PENDING_LAUNCH'}]
            }]
        }
        
        assert should_poll_now(execution) is True
    
    def test_should_not_poll_started_phase_too_soon(self):
        """Test skipping poll if < 15s for STARTED phase."""
        from execution_finder import should_poll_now
        from datetime import datetime, timezone
        
        # Set last poll to 10 seconds ago (< 15s threshold)
        last_poll = datetime.now(timezone.utc).timestamp() - 10
        
        execution = {
            'ExecutionId': 'test-123',
            'LastPolledTime': last_poll,
            'Waves': [{
                'Servers': [{'Status': 'LAUNCHING'}]
            }]
        }
        
        assert should_poll_now(execution) is False
    
    def test_should_poll_in_progress_phase_interval(self):
        """Test 30s interval for IN_PROGRESS phase."""
        from execution_finder import should_poll_now
        from datetime import datetime, timezone
        
        # Set last poll to 31 seconds ago (> 30s threshold)
        last_poll = datetime.now(timezone.utc).timestamp() - 31
        
        execution = {
            'ExecutionId': 'test-123',
            'LastPolledTime': last_poll,
            'Waves': [{
                'Servers': [{'Status': 'LAUNCHED'}]
            }]
        }
        
        assert should_poll_now(execution) is True
    
    def test_should_not_poll_in_progress_too_soon(self):
        """Test skipping poll if < 30s for IN_PROGRESS phase."""
        from execution_finder import should_poll_now
        from datetime import datetime, timezone
        
        # Set last poll to 25 seconds ago (< 30s threshold)
        last_poll = datetime.now(timezone.utc).timestamp() - 25
        
        execution = {
            'ExecutionId': 'test-123',
            'LastPolledTime': last_poll,
            'Waves': [{
                'Servers': [{'Status': 'RECOVERING'}]
            }]
        }
        
        assert should_poll_now(execution) is False
    
    def test_should_poll_error_fallback(self):
        """Test fail-safe: polls on error."""
        from execution_finder import should_poll_now
        
        # Malformed execution should trigger fail-safe
        execution = {
            'ExecutionId': 'test-123',
            'Waves': 'invalid'  # Should cause error
        }
        
        # Should return True on error (fail-safe)
        assert should_poll_now(execution) is True

class TestDetectExecutionPhase:
    """Tests for execution phase detection logic."""
    
    def test_detect_pending_phase_all_not_started(self):
        """Test PENDING when all servers NOT_STARTED."""
        from execution_finder import detect_execution_phase
        
        waves = [
            {'Servers': [{'Status': 'NOT_STARTED'}]},
            {'Servers': [{'Status': 'NOT_STARTED'}, {'Status': 'NOT_STARTED'}]}
        ]
        
        assert detect_execution_phase(waves) == 'PENDING'
    
    def test_detect_started_phase_pending_launch(self):
        """Test STARTED when servers in PENDING_LAUNCH."""
        from execution_finder import detect_execution_phase
        
        waves = [
            {'Servers': [{'Status': 'PENDING_LAUNCH'}]},
            {'Servers': [{'Status': 'NOT_STARTED'}]}
        ]
        
        assert detect_execution_phase(waves) == 'STARTED'
    
    def test_detect_started_phase_launching(self):
        """Test STARTED when servers LAUNCHING."""
        from execution_finder import detect_execution_phase
        
        waves = [
            {'Servers': [{'Status': 'LAUNCHING'}]},
            {'Servers': [{'Status': 'NOT_STARTED'}]}
        ]
        
        assert detect_execution_phase(waves) == 'STARTED'
    
    def test_detect_in_progress_phase_launched(self):
        """Test IN_PROGRESS when servers LAUNCHED."""
        from execution_finder import detect_execution_phase
        
        waves = [
            {'Servers': [{'Status': 'LAUNCHED'}]},
            {'Servers': [{'Status': 'NOT_STARTED'}]}
        ]
        
        assert detect_execution_phase(waves) == 'IN_PROGRESS'
    
    def test_detect_in_progress_phase_recovering(self):
        """Test IN_PROGRESS when servers RECOVERING."""
        from execution_finder import detect_execution_phase
        
        waves = [
            {'Servers': [{'Status': 'RECOVERING'}]},
            {'Servers': [{'Status': 'LAUNCHED'}]}
        ]
        
        assert detect_execution_phase(waves) == 'IN_PROGRESS'
    
    def test_detect_in_progress_phase_recovery_in_progress(self):
        """Test IN_PROGRESS when servers in RECOVERY_IN_PROGRESS."""
        from execution_finder import detect_execution_phase
        
        waves = [
            {'Servers': [{'Status': 'RECOVERY_IN_PROGRESS'}]}
        ]
        
        assert detect_execution_phase(waves) == 'IN_PROGRESS'
    
    def test_detect_phase_empty_waves(self):
        """Test PENDING when no waves provided."""
        from execution_finder import detect_execution_phase
        
        assert detect_execution_phase([]) == 'PENDING'
    
    def test_detect_phase_empty_servers(self):
        """Test PENDING when waves have no servers."""
        from execution_finder import detect_execution_phase
        
        waves = [{'Servers': []}]
        assert detect_execution_phase(waves) == 'PENDING'
    
    def test_detect_phase_priority_started_over_in_progress(self):
        """Test STARTED takes priority over IN_PROGRESS."""
        from execution_finder import detect_execution_phase
        
        # Mix of STARTED and IN_PROGRESS statuses
        waves = [
            {'Servers': [{'Status': 'LAUNCHING'}]},  # STARTED
            {'Servers': [{'Status': 'LAUNCHED'}]}    # IN_PROGRESS
        ]
        
        # STARTED has priority (critical transition)
        assert detect_execution_phase(waves) == 'STARTED'
    
    def test_detect_phase_error_fallback(self):
        """Test IN_PROGRESS fallback on error."""
        from execution_finder import detect_execution_phase
        
        # Malformed waves should trigger error handling
        waves = [{'Servers': 'invalid'}]
        
        # Should return IN_PROGRESS (most aggressive polling)
        assert detect_execution_phase(waves) == 'IN_PROGRESS'

class TestInvokePoller:
    """Tests for Lambda invocation logic."""
    
    @patch('execution_finder.lambda_client')
    def test_invoke_single_execution_success(self, mock_lambda):
        """Test successful invocation for single execution."""
        from execution_finder import invoke_pollers_for_executions
        
        mock_lambda.invoke.return_value = {'StatusCode': 202}
        
        executions = [{
            'ExecutionId': 'test-123',
            'PlanId': 'plan-456',
            'ExecutionType': 'DRILL',
            'StartTime': 1764345881
        }]
        
        result = invoke_pollers_for_executions(executions)
        
        assert result['successful'] == 1
        assert result['failed'] == 0
        assert len(result['details']['successful']) == 1
        assert result['details']['successful'][0]['ExecutionId'] == 'test-123'
        
        # Verify Lambda invoked with correct payload
        mock_lambda.invoke.assert_called_once()
        call_args = mock_lambda.invoke.call_args[1]
        assert call_args['InvocationType'] == 'Event'  # Async
        
        payload = json.loads(call_args['Payload'])
        assert payload['ExecutionId'] == 'test-123'
        assert payload['PlanId'] == 'plan-456'
    
    @patch('execution_finder.lambda_client')
    def test_invoke_multiple_executions_success(self, mock_lambda):
        """Test successful invocation for multiple executions."""
        from execution_finder import invoke_pollers_for_executions
        
        mock_lambda.invoke.return_value = {'StatusCode': 202}
        
        executions = [
            {'ExecutionId': 'test-1', 'PlanId': 'plan-1', 'ExecutionType': 'DRILL'},
            {'ExecutionId': 'test-2', 'PlanId': 'plan-2', 'ExecutionType': 'RECOVERY'},
            {'ExecutionId': 'test-3', 'PlanId': 'plan-3', 'ExecutionType': 'DRILL'}
        ]
        
        result = invoke_pollers_for_executions(executions)
        
        assert result['successful'] == 3
        assert result['failed'] == 0
        assert mock_lambda.invoke.call_count == 3
    
    @patch('execution_finder.lambda_client')
    def test_invoke_execution_failure(self, mock_lambda):
        """Test handling of Lambda invocation failure."""
        from execution_finder import invoke_pollers_for_executions
        
        mock_lambda.invoke.side_effect = Exception("Lambda invocation failed")
        
        executions = [{
            'ExecutionId': 'test-123',
            'PlanId': 'plan-456',
            'ExecutionType': 'DRILL'
        }]
        
        result = invoke_pollers_for_executions(executions)
        
        assert result['successful'] == 0
        assert result['failed'] == 1
        assert len(result['details']['failed']) == 1
        assert 'Lambda invocation failed' in result['details']['failed'][0]['Error']
    
    @patch('execution_finder.lambda_client')
    def test_invoke_partial_failure(self, mock_lambda):
        """Test mixed success/failure invocations."""
        from execution_finder import invoke_pollers_for_executions
        
        # First two succeed, third fails
        mock_lambda.invoke.side_effect = [
            {'StatusCode': 202},
            {'StatusCode': 202},
            Exception("Third invocation failed")
        ]
        
        executions = [
            {'ExecutionId': 'test-1', 'PlanId': 'plan-1'},
            {'ExecutionId': 'test-2', 'PlanId': 'plan-2'},
            {'ExecutionId': 'test-3', 'PlanId': 'plan-3'}
        ]
        
        result = invoke_pollers_for_executions(executions)
        
        assert result['successful'] == 2
        assert result['failed'] == 1
        assert len(result['details']['successful']) == 2
        assert len(result['details']['failed']) == 1
    
    @patch('execution_finder.lambda_client')
    def test_invoke_empty_list(self, mock_lambda):
        """Test invocation with empty execution list."""
        from execution_finder import invoke_pollers_for_executions
        
        result = invoke_pollers_for_executions([])
        
        assert result['successful'] == 0
        assert result['failed'] == 0
        mock_lambda.invoke.assert_not_called()

class TestLambdaHandlerEnhanced:
    """Tests for enhanced Lambda handler with new features."""
    
    @patch('execution_finder.lambda_client')
    @patch('execution_finder.dynamodb')
    def test_handler_with_adaptive_polling(self, mock_dynamodb, mock_lambda):
        """Test handler skips recent polls based on adaptive intervals."""
        from datetime import datetime, timezone
        
        # Setup execution that was polled 10 seconds ago (too recent for 15s interval)
        recent_poll = datetime.now(timezone.utc).timestamp() - 10
        
        mock_dynamodb.query.return_value = {
            'Count': 1,
            'Items': [{
                'ExecutionId': {'S': 'test-123'},
                'PlanId': {'S': 'plan-456'},
                'Status': {'S': 'POLLING'},
                'LastPolledTime': {'N': str(int(recent_poll))},
                'Waves': {
                    'L': [{
                        'M': {
                            'Servers': {
                                'L': [{'M': {'Status': {'S': 'LAUNCHING'}}}]  # STARTED phase = 15s
                            }
                        }
                    }]
                }
            }]
        }
        
        result = lambda_handler({}, Mock())
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        
        # Should skip this execution (too recent)
        assert body['executionsSkipped'] == 1
        assert body['executionsPolled'] == 0
        
        # Lambda should NOT be invoked
        mock_lambda.invoke.assert_not_called()
    
    @patch('execution_finder.lambda_client')
    @patch('execution_finder.dynamodb')
    def test_handler_invokes_pollers(self, mock_dynamodb, mock_lambda):
        """Test handler invokes pollers for executions."""
        from datetime import datetime, timezone
        
        # Setup execution ready to poll (60s ago, any interval)
        old_poll = datetime.now(timezone.utc).timestamp() - 60
        
        mock_dynamodb.query.return_value = {
            'Count': 1,
            'Items': [{
                'ExecutionId': {'S': 'test-123'},
                'PlanId': {'S': 'plan-456'},
                'Status': {'S': 'POLLING'},
                'LastPolledTime': {'N': str(int(old_poll))},
                'Waves': {'L': []}
            }]
        }
        
        mock_lambda.invoke.return_value = {'StatusCode': 202}
        
        result = lambda_handler({}, Mock())
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        
        # Should poll this execution
        assert body['executionsPolled'] == 1
        assert body['invocations']['successful'] == 1
        
        # Lambda should be invoked
        mock_lambda.invoke.assert_called_once()

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
