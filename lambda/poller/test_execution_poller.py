"""
Unit tests for Execution Poller Lambda
Tests DRS polling logic, timeout handling, and status updates.
"""
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
from execution_poller import (
    lambda_handler,
    get_execution_from_dynamodb,
    parse_dynamodb_item,
    parse_dynamodb_value,
    has_execution_timed_out,
    handle_timeout,
    poll_wave_status,
    query_drs_job_status,
    update_execution_waves,
    update_last_polled_time,
    finalize_execution,
    record_poller_metrics,
    format_wave_for_dynamodb,
    format_value_for_dynamodb
)

# Sample test data - using current time to avoid timeout issues
def get_current_time_event():
    """Generate event with current timestamp to avoid timeout."""
    current_time = int(datetime.now(timezone.utc).timestamp())
    return {
        'ExecutionId': 'test-execution-123',
        'PlanId': 'plan-456',
        'ExecutionType': 'DRILL',
        'StartTime': current_time - 300  # 5 minutes ago
    }

SAMPLE_EXECUTION_EVENT = get_current_time_event()

def get_current_time_execution():
    """Generate execution with current timestamp to avoid timeout."""
    current_time = int(datetime.now(timezone.utc).timestamp())
    start_time = current_time - 300  # 5 minutes ago
    return {
        'ExecutionId': {'S': 'test-execution-123'},
        'PlanId': {'S': 'plan-456'},
        'Status': {'S': 'POLLING'},
        'StartTime': {'N': str(start_time)},
        'ExecutionType': {'S': 'DRILL'},
        'LastPolledTime': {'N': str(current_time - 60)},
        'Waves': {
            'L': [
                {
                    'M': {
                        'WaveId': {'S': 'wave-1'},
                        'WaveName': {'S': 'Database'},
                        'Status': {'S': 'INITIATED'},
                        'JobId': {'S': 'job-123'},
                        'Servers': {
                            'L': [
                                {
                                    'M': {
                                        'SourceServerID': {'S': 'server-1'},
                                        'Status': {'S': 'PENDING_LAUNCH'},
                                        'HostName': {'S': 'db-server-1'}
                                    }
                                }
                            ]
                        }
                    }
                }
            ]
        }
    }

SAMPLE_DYNAMODB_EXECUTION = {
    'ExecutionId': {'S': 'test-execution-123'},
    'PlanId': {'S': 'plan-456'},
    'Status': {'S': 'POLLING'},
    'StartTime': {'N': str(int(datetime.now(timezone.utc).timestamp()) - 300)},
    'ExecutionType': {'S': 'DRILL'},
    'LastPolledTime': {'N': str(int(datetime.now(timezone.utc).timestamp()) - 60)},
    'Waves': {
        'L': [
            {
                'M': {
                    'WaveId': {'S': 'wave-1'},
                    'WaveName': {'S': 'Database'},
                    'Status': {'S': 'INITIATED'},
                    'JobId': {'S': 'job-123'},
                    'Servers': {
                        'L': [
                            {
                                'M': {
                                    'SourceServerID': {'S': 'server-1'},
                                    'Status': {'S': 'PENDING_LAUNCH'},
                                    'HostName': {'S': 'db-server-1'}
                                }
                            }
                        ]
                    }
                }
            }
        ]
    }
}

SAMPLE_DRS_JOB_RESPONSE = {
    'items': [
        {
            'jobID': 'job-123',
            'status': 'LAUNCHING',
            'statusMessage': 'Launching instances',
            'participatingServers': [
                {
                    'SourceServerID': 'server-1',
                    'LaunchStatus': 'LAUNCHING',
                    'HostName': 'db-server-1',
                    'LaunchTime': 1764345920
                }
            ],
            'postLaunchActionsStatus': 'NOT_STARTED'
        }
    ]
}

@pytest.fixture
def mock_env(monkeypatch):
    """Set up environment variables for tests."""
    monkeypatch.setenv('EXECUTION_HISTORY_TABLE', 'test-execution-table')
    monkeypatch.setenv('TIMEOUT_THRESHOLD_SECONDS', '1800')

@pytest.fixture
def mock_clients():
    """Mock all AWS clients."""
    with patch('execution_poller.dynamodb') as mock_dynamodb, \
         patch('execution_poller.drs') as mock_drs, \
         patch('execution_poller.cloudwatch') as mock_cloudwatch:
        yield {
            'dynamodb': mock_dynamodb,
            'drs': mock_drs,
            'cloudwatch': mock_cloudwatch
        }

class TestLambdaHandler:
    """Tests for main Lambda handler function."""
    
    def test_handler_success_polling_in_progress(self, mock_env, mock_clients):
        """Test successful polling with waves still in progress."""
        mock_clients['dynamodb'].get_item.return_value = {'Item': get_current_time_execution()}
        mock_clients['drs'].describe_jobs.return_value = SAMPLE_DRS_JOB_RESPONSE
        mock_clients['dynamodb'].update_item.return_value = {}
        mock_clients['cloudwatch'].put_metric_data.return_value = {}
        
        result = lambda_handler(SAMPLE_EXECUTION_EVENT, Mock())
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['ExecutionId'] == 'test-execution-123'
        assert body['Status'] == 'POLLING'
        assert body['WavesPolled'] == 1
    
    def test_handler_success_execution_complete(self, mock_env, mock_clients):
        """Test successful polling when all waves complete."""
        # Setup execution with completed waves
        completed_execution = get_current_time_execution()
        completed_execution['Waves']['L'][0]['M']['Status'] = {'S': 'COMPLETED'}
        completed_execution['Waves']['L'][0]['M']['Servers']['L'][0]['M']['Status'] = {'S': 'LAUNCHED'}
        
        mock_clients['dynamodb'].get_item.return_value = {'Item': completed_execution}
        # DRS returns all servers LAUNCHED
        mock_clients['drs'].describe_jobs.return_value = {
            'items': [{
                'jobID': 'job-123',
                'status': 'COMPLETED',
                'participatingServers': [
                    {'SourceServerID': 'server-1', 'LaunchStatus': 'LAUNCHED'}
                ],
                'postLaunchActionsStatus': 'NOT_STARTED'
            }]
        }
        mock_clients['dynamodb'].update_item.return_value = {}
        
        result = lambda_handler(SAMPLE_EXECUTION_EVENT, Mock())
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['Status'] == 'COMPLETED'
    
    def test_handler_execution_not_found(self, mock_env, mock_clients):
        """Test handler when execution not found in DynamoDB."""
        mock_clients['dynamodb'].get_item.return_value = {}  # No 'Item' key
        
        result = lambda_handler(SAMPLE_EXECUTION_EVENT, Mock())
        
        assert result['statusCode'] == 404
        body = json.loads(result['body'])
        assert 'Execution not found' in body['error']
    
    def test_handler_execution_timeout(self, mock_env, mock_clients):
        """Test handler when execution has timed out."""
        # Setup execution with old start time (> 30 minutes ago)
        old_start_time = int(datetime.now(timezone.utc).timestamp()) - 2000  # 33 minutes ago
        
        timeout_event = SAMPLE_EXECUTION_EVENT.copy()
        timeout_event['StartTime'] = old_start_time
        
        timeout_execution = SAMPLE_DYNAMODB_EXECUTION.copy()
        timeout_execution['StartTime'] = {'N': str(old_start_time)}
        
        mock_clients['dynamodb'].get_item.return_value = {'Item': timeout_execution}
        mock_clients['drs'].describe_jobs.return_value = SAMPLE_DRS_JOB_RESPONSE
        mock_clients['dynamodb'].update_item.return_value = {}
        
        result = lambda_handler(timeout_event, Mock())
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['Status'] == 'TIMEOUT'
    
    def test_handler_error(self, mock_env, mock_clients):
        """Test error handling in Lambda handler."""
        mock_clients['dynamodb'].get_item.side_effect = Exception("DynamoDB error")
        
        result = lambda_handler(SAMPLE_EXECUTION_EVENT, Mock())
        
        assert result['statusCode'] == 500
        body = json.loads(result['body'])
        assert 'error' in body
        assert 'Failed to poll execution' in body['message']
    
    def test_handler_missing_execution_id(self, mock_env, mock_clients):
        """Test handler with missing ExecutionId in event."""
        invalid_event = {'PlanId': 'plan-456'}  # Missing ExecutionId
        
        result = lambda_handler(invalid_event, Mock())
        
        assert result['statusCode'] == 500
        body = json.loads(result['body'])
        assert 'error' in body
    
    def test_handler_drill_mode_completion(self, mock_env, mock_clients):
        """Test DRILL mode completes when all servers LAUNCHED."""
        # Setup DRILL execution with all servers LAUNCHED
        drill_execution = get_current_time_execution()
        drill_execution['ExecutionType'] = {'S': 'DRILL'}
        drill_execution['Waves']['L'][0]['M']['Servers']['L'][0]['M']['Status'] = {'S': 'LAUNCHED'}
        
        mock_clients['dynamodb'].get_item.return_value = {'Item': drill_execution}
        mock_clients['drs'].describe_jobs.return_value = {
            'items': [{
                'jobID': 'job-123',
                'status': 'COMPLETED',
                'participatingServers': [{'SourceServerID': 'server-1', 'LaunchStatus': 'LAUNCHED'}],
                'postLaunchActionsStatus': 'NOT_STARTED'
            }]
        }
        mock_clients['dynamodb'].update_item.return_value = {}
        
        result = lambda_handler(SAMPLE_EXECUTION_EVENT, Mock())
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['Status'] == 'COMPLETED'
    
    def test_handler_recovery_mode_completion(self, mock_env, mock_clients):
        """Test RECOVERY mode completes with LAUNCHED + post-launch."""
        # Setup RECOVERY execution with post-launch complete
        recovery_event = get_current_time_event()
        recovery_event['ExecutionType'] = 'RECOVERY'
        
        recovery_execution = get_current_time_execution()
        recovery_execution['ExecutionType'] = {'S': 'RECOVERY'}
        recovery_execution['Waves']['L'][0]['M']['Servers']['L'][0]['M']['Status'] = {'S': 'LAUNCHED'}
        
        mock_clients['dynamodb'].get_item.return_value = {'Item': recovery_execution}
        mock_clients['drs'].describe_jobs.return_value = {
            'items': [{
                'jobID': 'job-123',
                'status': 'COMPLETED',
                'participatingServers': [{'SourceServerID': 'server-1', 'LaunchStatus': 'LAUNCHED'}],
                'postLaunchActionsStatus': 'COMPLETED'
            }]
        }
        mock_clients['dynamodb'].update_item.return_value = {}
        
        result = lambda_handler(recovery_event, Mock())
        
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['Status'] == 'COMPLETED'

class TestGetExecutionFromDynamoDB:
    """Tests for DynamoDB execution retrieval."""
    
    def test_get_execution_success(self, mock_env, mock_clients):
        """Test successful execution retrieval."""
        mock_clients['dynamodb'].get_item.return_value = {'Item': SAMPLE_DYNAMODB_EXECUTION}
        
        execution = get_execution_from_dynamodb('test-execution-123', 'plan-456')
        
        assert execution is not None
        assert execution['ExecutionId'] == 'test-execution-123'
        assert execution['Status'] == 'POLLING'
        assert len(execution['Waves']) == 1
    
    def test_get_execution_not_found(self, mock_env, mock_clients):
        """Test execution not found returns None."""
        mock_clients['dynamodb'].get_item.return_value = {}  # No 'Item' key
        
        execution = get_execution_from_dynamodb('nonexistent', 'plan-456')
        
        assert execution is None
    
    def test_get_execution_dynamodb_error(self, mock_env, mock_clients):
        """Test DynamoDB error handling."""
        mock_clients['dynamodb'].get_item.side_effect = Exception("DynamoDB error")
        
        with pytest.raises(Exception) as exc_info:
            get_execution_from_dynamodb('test-execution-123', 'plan-456')
        
        assert "DynamoDB error" in str(exc_info.value)
    
    def test_get_execution_complex_structure(self, mock_env, mock_clients):
        """Test parsing complex nested execution structure."""
        mock_clients['dynamodb'].get_item.return_value = {'Item': SAMPLE_DYNAMODB_EXECUTION}
        
        execution = get_execution_from_dynamodb('test-execution-123', 'plan-456')
        
        # Verify nested structure parsed correctly
        assert execution['Waves'][0]['WaveName'] == 'Database'
        assert execution['Waves'][0]['Servers'][0]['SourceServerID'] == 'server-1'
        # Verify StartTime is an integer (timestamp)
        assert isinstance(execution['StartTime'], int)
        assert execution['StartTime'] > 0
    
    def test_get_execution_verify_key_structure(self, mock_env, mock_clients):
        """Test correct DynamoDB key structure used."""
        mock_clients['dynamodb'].get_item.return_value = {'Item': SAMPLE_DYNAMODB_EXECUTION}
        
        get_execution_from_dynamodb('test-execution-123', 'plan-456')
        
        # Verify get_item called with correct key structure
        call_args = mock_clients['dynamodb'].get_item.call_args[1]
        assert call_args['Key'] == {
            'ExecutionId': {'S': 'test-execution-123'},
            'PlanId': {'S': 'plan-456'}
        }

class TestHasExecutionTimedOut:
    """Tests for timeout detection."""
    
    def test_timeout_within_threshold(self, mock_env):
        """Test execution within timeout threshold."""
        current_time = datetime.now(timezone.utc).timestamp()
        start_time = int(current_time - 900)  # 15 minutes ago
        
        execution = {'StartTime': start_time}
        
        assert has_execution_timed_out(execution, start_time) is False
    
    def test_timeout_at_threshold(self, mock_env):
        """Test execution exactly at timeout threshold."""
        current_time = datetime.now(timezone.utc).timestamp()
        start_time = int(current_time - 1800)  # Exactly 30 minutes
        
        execution = {'StartTime': start_time}
        
        # At threshold (>=1800) should timeout (True)
        assert has_execution_timed_out(execution, start_time) is True
    
    def test_timeout_beyond_threshold(self, mock_env):
        """Test execution beyond timeout threshold."""
        current_time = datetime.now(timezone.utc).timestamp()
        start_time = int(current_time - 2000)  # 33+ minutes ago
        
        execution = {'StartTime': start_time}
        
        assert has_execution_timed_out(execution, start_time) is True
    
    def test_timeout_missing_start_time_param(self, mock_env):
        """Test timeout check with start_time from execution."""
        current_time = datetime.now(timezone.utc).timestamp()
        start_time = int(current_time - 2000)
        
        execution = {'StartTime': start_time}
        
        # No start_time parameter, should use from execution
        assert has_execution_timed_out(execution, None) is True
    
    def test_timeout_zero_start_time(self, mock_env):
        """Test timeout with zero start time."""
        execution = {'StartTime': 0}
        
        # Very old start time should timeout
        assert has_execution_timed_out(execution, 0) is True
    
    def test_timeout_custom_threshold(self, mock_env, monkeypatch):
        """Test timeout with custom threshold."""
        monkeypatch.setenv('TIMEOUT_THRESHOLD_SECONDS', '600')  # 10 minutes
        
        # Need to reload module to pick up new env var
        import importlib
        import execution_poller
        importlib.reload(execution_poller)
        
        current_time = datetime.now(timezone.utc).timestamp()
        start_time = int(current_time - 700)  # 11+ minutes ago
        
        execution = {'StartTime': start_time}
        
        assert execution_poller.has_execution_timed_out(execution, start_time) is True

class TestHandleTimeout:
    """Tests for timeout handling logic."""
    
    def test_handle_timeout_queries_drs(self, mock_env, mock_clients):
        """Test timeout handler queries DRS for final status."""
        execution = {
            'Waves': [
                {'JobId': 'job-123', 'Status': 'INITIATED'}
            ]
        }
        
        mock_clients['drs'].describe_jobs.return_value = {
            'items': [{'jobID': 'job-123', 'status': 'FAILED', 'statusMessage': 'Timeout'}]
        }
        mock_clients['dynamodb'].update_item.return_value = {}
        
        handle_timeout('test-exec', 'plan-123', execution)
        
        # Verify DRS was queried
        mock_clients['drs'].describe_jobs.assert_called_once()
        
        # Verify DynamoDB updated with timeout status
        call_args = mock_clients['dynamodb'].update_item.call_args[1]
        assert call_args['ExpressionAttributeValues'][':status'] == {'S': 'TIMEOUT'}
    
    def test_handle_timeout_no_job_id(self, mock_env, mock_clients):
        """Test timeout handling when wave has no JobId."""
        execution = {
            'Waves': [
                {'WaveId': 'wave-1', 'Status': 'INITIATED'}  # No JobId
            ]
        }
        
        mock_clients['dynamodb'].update_item.return_value = {}
        
        handle_timeout('test-exec', 'plan-123', execution)
        
        # Should not query DRS without JobId
        mock_clients['drs'].describe_jobs.assert_not_called()
        
        # Should still update with TIMEOUT status
        call_args = mock_clients['dynamodb'].update_item.call_args[1]
        assert call_args['ExpressionAttributeValues'][':status'] == {'S': 'TIMEOUT'}
    
    def test_handle_timeout_drs_error(self, mock_env, mock_clients):
        """Test timeout handling when DRS query fails."""
        execution = {
            'Waves': [
                {'JobId': 'job-123', 'Status': 'INITIATED'}
            ]
        }
        
        mock_clients['drs'].describe_jobs.side_effect = Exception("DRS error")
        mock_clients['dynamodb'].update_item.return_value = {}
        
        # Should not raise, should handle gracefully
        handle_timeout('test-exec', 'plan-123', execution)
        
        # Should still update with TIMEOUT
        call_args = mock_clients['dynamodb'].update_item.call_args[1]
        assert call_args['ExpressionAttributeValues'][':status'] == {'S': 'TIMEOUT'}
    
    def test_handle_timeout_multiple_waves(self, mock_env, mock_clients):
        """Test timeout handling with multiple waves."""
        execution = {
            'Waves': [
                {'JobId': 'job-1', 'Status': 'INITIATED'},
                {'JobId': 'job-2', 'Status': 'PENDING'}
            ]
        }
        
        mock_clients['drs'].describe_jobs.side_effect = [
            {'items': [{'jobID': 'job-1', 'status': 'COMPLETED'}]},
            {'items': [{'jobID': 'job-2', 'status': 'FAILED'}]}
        ]
        mock_clients['dynamodb'].update_item.return_value = {}
        
        handle_timeout('test-exec', 'plan-123', execution)
        
        # Should query DRS for both waves
        assert mock_clients['drs'].describe_jobs.call_count == 2
    
    def test_handle_timeout_sets_end_time(self, mock_env, mock_clients):
        """Test timeout sets EndTime timestamp."""
        execution = {'Waves': []}
        
        mock_clients['dynamodb'].update_item.return_value = {}
        
        before_time = int(datetime.now(timezone.utc).timestamp())
        handle_timeout('test-exec', 'plan-123', execution)
        after_time = int(datetime.now(timezone.utc).timestamp())
        
        # Verify EndTime set in DynamoDB update
        call_args = mock_clients['dynamodb'].update_item.call_args[1]
        end_time = int(call_args['ExpressionAttributeValues'][':end_time']['N'])
        
        assert before_time <= end_time <= after_time
    
    def test_handle_timeout_updates_all_waves(self, mock_env, mock_clients):
        """Test timeout updates all waves in execution."""
        execution = {
            'Waves': [
                {'JobId': 'job-1', 'Status': 'INITIATED'},
                {'JobId': 'job-2', 'Status': 'PENDING'},
                {'WaveId': 'wave-3', 'Status': 'INITIATED'}  # No JobId
            ]
        }
        
        mock_clients['drs'].describe_jobs.return_value = {
            'items': [{'jobID': 'job-1', 'status': 'COMPLETED'}]
        }
        mock_clients['dynamodb'].update_item.return_value = {}
        
        handle_timeout('test-exec', 'plan-123', execution)
        
        # Verify all waves updated in DynamoDB
        call_args = mock_clients['dynamodb'].update_item.call_args[1]
        waves_list = call_args['ExpressionAttributeValues'][':waves']['L']
        assert len(waves_list) == 3

class TestPollWaveStatus:
    """Tests for wave status polling."""
    
    def test_poll_wave_success_drill_mode(self, mock_env, mock_clients):
        """Test successful wave polling in DRILL mode."""
        wave = {
            'WaveId': 'wave-1',
            'JobId': 'job-123',
            'Status': 'INITIATED',
            'Servers': [{'SourceServerID': 'server-1', 'Status': 'PENDING_LAUNCH'}]
        }
        
        mock_clients['drs'].describe_jobs.return_value = {
            'items': [{
                'jobID': 'job-123',
                'status': 'COMPLETED',
                'statusMessage': 'All servers launched',
                'participatingServers': [
                    {'SourceServerID': 'server-1', 'LaunchStatus': 'LAUNCHED', 'HostName': 'server-1'}
                ],
                'postLaunchActionsStatus': 'NOT_STARTED'
            }]
        }
        
        updated_wave = poll_wave_status(wave, 'DRILL')
        
        assert updated_wave['Status'] == 'COMPLETED'
        assert updated_wave['Servers'][0]['Status'] == 'LAUNCHED'
    
    def test_poll_wave_success_recovery_mode(self, mock_env, mock_clients):
        """Test successful wave polling in RECOVERY mode."""
        wave = {
            'WaveId': 'wave-1',
            'JobId': 'job-123',
            'Status': 'INITIATED',
            'Servers': [{'SourceServerID': 'server-1', 'Status': 'LAUNCHED'}]
        }
        
        mock_clients['drs'].describe_jobs.return_value = {
            'items': [{
                'jobID': 'job-123',
                'status': 'COMPLETED',
                'participatingServers': [
                    {'SourceServerID': 'server-1', 'LaunchStatus': 'LAUNCHED'}
                ],
                'postLaunchActionsStatus': 'COMPLETED'
            }]
        }
        
        updated_wave = poll_wave_status(wave, 'RECOVERY')
        
        assert updated_wave['Status'] == 'COMPLETED'
    
    def test_poll_wave_no_job_id(self, mock_env, mock_clients):
        """Test polling wave without JobId."""
        wave = {'WaveId': 'wave-1', 'Status': 'PENDING'}
        
        updated_wave = poll_wave_status(wave, 'DRILL')
        
        # Should return wave unchanged
        assert updated_wave == wave
        mock_clients['drs'].describe_jobs.assert_not_called()
    
    def test_poll_wave_in_progress(self, mock_env, mock_clients):
        """Test polling wave still in progress."""
        wave = {
            'WaveId': 'wave-1',
            'JobId': 'job-123',
            'Servers': [{'SourceServerID': 'server-1', 'Status': 'PENDING_LAUNCH'}]
        }
        
        mock_clients['drs'].describe_jobs.return_value = {
            'items': [{
                'jobID': 'job-123',
                'status': 'LAUNCHING',
                'participatingServers': [
                    {'SourceServerID': 'server-1', 'LaunchStatus': 'LAUNCHING'}
                ]
            }]
        }
        
        updated_wave = poll_wave_status(wave, 'DRILL')
        
        # Should not be complete yet
        assert updated_wave['Status'] == 'LAUNCHING'
    
    def test_poll_wave_drs_error(self, mock_env, mock_clients):
        """Test wave polling with DRS error."""
        wave = {'WaveId': 'wave-1', 'JobId': 'job-123', 'Status': 'INITIATED'}
        
        mock_clients['drs'].describe_jobs.side_effect = Exception("DRS API error")
        
        updated_wave = poll_wave_status(wave, 'DRILL')
        
        assert updated_wave['Status'] == 'ERROR'
        assert 'Polling error' in updated_wave['StatusMessage']
    
    def test_poll_wave_updates_server_statuses(self, mock_env, mock_clients):
        """Test wave polling updates server statuses."""
        wave = {
            'WaveId': 'wave-1',
            'JobId': 'job-123',
            'Servers': [
                {'SourceServerID': 'server-1', 'Status': 'PENDING_LAUNCH'},
                {'SourceServerID': 'server-2', 'Status': 'PENDING_LAUNCH'}
            ]
        }
        
        mock_clients['drs'].describe_jobs.return_value = {
            'items': [{
                'jobID': 'job-123',
                'status': 'LAUNCHING',
                'participatingServers': [
                    {'SourceServerID': 'server-1', 'LaunchStatus': 'LAUNCHED', 'HostName': 'host-1', 'LaunchTime': 12345},
                    {'SourceServerID': 'server-2', 'LaunchStatus': 'LAUNCHING', 'HostName': 'host-2', 'LaunchTime': 12346}
                ]
            }]
        }
        
        updated_wave = poll_wave_status(wave, 'DRILL')
        
        assert len(updated_wave['Servers']) == 2
        assert updated_wave['Servers'][0]['Status'] == 'LAUNCHED'
        assert updated_wave['Servers'][1]['Status'] == 'LAUNCHING'
        assert updated_wave['Servers'][0]['HostName'] == 'host-1'
    
    def test_poll_wave_drill_incomplete_servers(self, mock_env, mock_clients):
        """Test DRILL mode doesn't complete with mixed server statuses."""
        wave = {
            'WaveId': 'wave-1',
            'JobId': 'job-123',
            'Servers': []
        }
        
        mock_clients['drs'].describe_jobs.return_value = {
            'items': [{
                'jobID': 'job-123',
                'status': 'LAUNCHING',
                'participatingServers': [
                    {'SourceServerID': 'server-1', 'LaunchStatus': 'LAUNCHED'},
                    {'SourceServerID': 'server-2', 'LaunchStatus': 'LAUNCHING'}  # Still launching
                ],
                'postLaunchActionsStatus': 'NOT_STARTED'
            }]
        }
        
        updated_wave = poll_wave_status(wave, 'DRILL')
        
        # Should not complete - one server still launching
        assert updated_wave['Status'] == 'LAUNCHING'
    
    def test_poll_wave_recovery_needs_post_launch(self, mock_env, mock_clients):
        """Test RECOVERY mode doesn't complete without post-launch."""
        wave = {
            'WaveId': 'wave-1',
            'JobId': 'job-123',
            'Servers': []
        }
        
        mock_clients['drs'].describe_jobs.return_value = {
            'items': [{
                'jobID': 'job-123',
                'status': 'COMPLETED',
                'participatingServers': [
                    {'SourceServerID': 'server-1', 'LaunchStatus': 'LAUNCHED'}
                ],
                'postLaunchActionsStatus': 'IN_PROGRESS'  # Not complete
            }]
        }
        
        updated_wave = poll_wave_status(wave, 'RECOVERY')
        
        # Should not complete - post-launch not done
        assert updated_wave['Status'] == 'COMPLETED'  # Job status
        # But wave not marked complete due to post-launch

class TestQueryDRSJobStatus:
    """Tests for DRS job status querying."""
    
    def test_query_job_success(self, mock_env, mock_clients):
        """Test successful DRS job query."""
        mock_clients['drs'].describe_jobs.return_value = SAMPLE_DRS_JOB_RESPONSE
        
        status = query_drs_job_status('job-123')
        
        assert status['Status'] == 'LAUNCHING'
        assert status['StatusMessage'] == 'Launching instances'
        assert len(status['ParticipatingServers']) == 1
        assert status['PostLaunchActionsStatus'] == 'NOT_STARTED'
    
    def test_query_job_not_found(self, mock_env, mock_clients):
        """Test query when job not found."""
        mock_clients['drs'].describe_jobs.return_value = {'items': []}
        
        status = query_drs_job_status('job-123')
        
        assert status['Status'] == 'UNKNOWN'
        assert 'Job not found' in status['StatusMessage']
    
    def test_query_job_drs_error(self, mock_env, mock_clients):
        """Test DRS API error handling."""
        mock_clients['drs'].describe_jobs.side_effect = Exception("DRS API error")
        
        with pytest.raises(Exception) as exc_info:
            query_drs_job_status('job-123')
        
        assert "DRS API error" in str(exc_info.value)
    
    def test_query_job_filters(self, mock_env, mock_clients):
        """Test DRS job query uses correct filters."""
        mock_clients['drs'].describe_jobs.return_value = SAMPLE_DRS_JOB_RESPONSE
        
        query_drs_job_status('job-123')
        
        # Verify correct filter used
        call_args = mock_clients['drs'].describe_jobs.call_args[1]
        assert call_args['filters'] == {'jobIDs': ['job-123']}
    
    def test_query_job_missing_fields(self, mock_env, mock_clients):
        """Test query with incomplete job data."""
        mock_clients['drs'].describe_jobs.return_value = {
            'items': [{'jobID': 'job-123'}]  # Missing most fields
        }
        
        status = query_drs_job_status('job-123')
        
        # Should handle missing fields gracefully
        assert status['Status'] == 'UNKNOWN'
        assert status['StatusMessage'] == ''
        assert status['ParticipatingServers'] == []

class TestUpdateExecutionWaves:
    """Tests for execution wave updates."""
    
    def test_update_waves_success(self, mock_env, mock_clients):
        """Test successful wave update."""
        waves = [
            {'WaveId': 'wave-1', 'Status': 'COMPLETED'},
            {'WaveId': 'wave-2', 'Status': 'IN_PROGRESS'}
        ]
        
        mock_clients['dynamodb'].update_item.return_value = {}
        
        update_execution_waves('exec-123', 'plan-456', waves)
        
        # Verify update called
        mock_clients['dynamodb'].update_item.assert_called_once()
    
    def test_update_waves_dynamodb_error(self, mock_env, mock_clients):
        """Test DynamoDB error handling."""
        waves = [{'WaveId': 'wave-1'}]
        
        mock_clients['dynamodb'].update_item.side_effect = Exception("DynamoDB error")
        
        with pytest.raises(Exception) as exc_info:
            update_execution_waves('exec-123', 'plan-456', waves)
        
        assert "DynamoDB error" in str(exc_info.value)
    
    def test_update_waves_empty_list(self, mock_env, mock_clients):
        """Test update with empty wave list."""
        mock_clients['dynamodb'].update_item.return_value = {}
        
        update_execution_waves('exec-123', 'plan-456', [])
        
        # Should still update
        mock_clients['dynamodb'].update_item.assert_called_once()
    
    def test_update_waves_key_structure(self, mock_env, mock_clients):
        """Test correct key structure used."""
        waves = [{'WaveId': 'wave-1'}]
        mock_clients['dynamodb'].update_item.return_value = {}
        
        update_execution_waves('exec-123', 'plan-456', waves)
        
        call_args = mock_clients['dynamodb'].update_item.call_args[1]
        assert call_args['Key'] == {
            'ExecutionId': {'S': 'exec-123'},
            'PlanId': {'S': 'plan-456'}
        }
    
    def test_update_waves_expression(self, mock_env, mock_clients):
        """Test update expression format."""
        waves = [{'WaveId': 'wave-1'}]
        mock_clients['dynamodb'].update_item.return_value = {}
        
        update_execution_waves('exec-123', 'plan-456', waves)
        
        call_args = mock_clients['dynamodb'].update_item.call_args[1]
        assert call_args['UpdateExpression'] == 'SET Waves = :waves'

class TestUpdateLastPolledTime:
    """Tests for last polled time updates."""
    
    def test_update_time_success(self, mock_env, mock_clients):
        """Test successful time update."""
        mock_clients['dynamodb'].update_item.return_value = {}
        
        before_time = int(datetime.now(timezone.utc).timestamp())
        update_last_polled_time('exec-123', 'plan-456')
        after_time = int(datetime.now(timezone.utc).timestamp())
        
        # Verify time updated
        call_args = mock_clients['dynamodb'].update_item.call_args[1]
        polled_time = int(call_args['ExpressionAttributeValues'][':time']['N'])
        
        assert before_time <= polled_time <= after_time
    
    def test_update_time_error_handled(self, mock_env, mock_clients):
        """Test error handling (non-critical)."""
        mock_clients['dynamodb'].update_item.side_effect = Exception("DynamoDB error")
        
        # Should not raise - non-critical error
        update_last_polled_time('exec-123', 'plan-456')

class TestFinalizeExecution:
    """Tests for execution finalization."""
    
    def test_finalize_all_completed(self, mock_env, mock_clients):
        """Test finalization when all waves completed."""
        waves = [
            {'WaveId': 'wave-1', 'Status': 'COMPLETED'},
            {'WaveId': 'wave-2', 'Status': 'COMPLETED'}
        ]
        
        mock_clients['dynamodb'].update_item.return_value = {}
        
        finalize_execution('exec-123', 'plan-456', waves)
        
        # Verify status set to COMPLETED
        call_args = mock_clients['dynamodb'].update_item.call_args[1]
        assert call_args['ExpressionAttributeValues'][':status'] == {'S': 'COMPLETED'}
    
    def test_finalize_with_failures(self, mock_env, mock_clients):
        """Test finalization when some waves failed."""
        waves = [
            {'WaveId': 'wave-1', 'Status': 'COMPLETED'},
            {'WaveId': 'wave-2', 'Status': 'FAILED'}
        ]
        
        mock_clients['dynamodb'].update_item.return_value = {}
        
        finalize_execution('exec-123', 'plan-456', waves)
        
        # Verify status set to FAILED
        call_args = mock_clients['dynamodb'].update_item.call_args[1]
        assert call_args['ExpressionAttributeValues'][':status'] == {'S': 'FAILED'}
    
    def test_finalize_with_warnings(self, mock_env, mock_clients):
        """Test finalization with mixed statuses."""
        waves = [
            {'WaveId': 'wave-1', 'Status': 'COMPLETED'},
            {'WaveId': 'wave-2', 'Status': 'TIMEOUT'}
        ]
        
        mock_clients['dynamodb'].update_item.return_value = {}
        
        finalize_execution('exec-123', 'plan-456', waves)
        
        # Verify status set to COMPLETED_WITH_WARNINGS
        call_args = mock_clients['dynamodb'].update_item.call_args[1]
        assert call_args['ExpressionAttributeValues'][':status'] == {'S': 'COMPLETED_WITH_WARNINGS'}
    
    def test_finalize_sets_end_time(self, mock_env, mock_clients):
        """Test finalization sets EndTime."""
        waves = [{'WaveId': 'wave-1', 'Status': 'COMPLETED'}]
        mock_clients['dynamodb'].update_item.return_value = {}
        
        before_time = int(datetime.now(timezone.utc).timestamp())
        finalize_execution('exec-123', 'plan-456', waves)
        after_time = int(datetime.now(timezone.utc).timestamp())
        
        call_args = mock_clients['dynamodb'].update_item.call_args[1]
        end_time = int(call_args['ExpressionAttributeValues'][':end_time']['N'])
        
        assert before_time <= end_time <= after_time
    
    def test_finalize_error(self, mock_env, mock_clients):
        """Test finalization error handling."""
        waves = [{'WaveId': 'wave-1', 'Status': 'COMPLETED'}]
        mock_clients['dynamodb'].update_item.side_effect = Exception("DynamoDB error")
        
        with pytest.raises(Exception):
            finalize_execution('exec-123', 'plan-456', waves)

class TestRecordPollerMetrics:
    """Tests for CloudWatch metrics recording."""
    
    def test_record_metrics_success(self, mock_env, mock_clients):
        """Test successful metrics recording."""
        waves = [
            {'WaveId': 'wave-1', 'Servers': [{'Status': 'LAUNCHED'}]},
            {'WaveId': 'wave-2', 'Servers': [{'Status': 'LAUNCHING'}]}
        ]
        
        mock_clients['cloudwatch'].put_metric_data.return_value = {}
        
        record_poller_metrics('exec-123', 'DRILL', waves)
        
        # Verify metrics published
        mock_clients['cloudwatch'].put_metric_data.assert_called_once()
    
    def test_record_metrics_error_handled(self, mock_env, mock_clients):
        """Test metrics error handling (non-critical)."""
        waves = []
        mock_clients['cloudwatch'].put_metric_data.side_effect = Exception("CloudWatch error")
        
        # Should not raise - non-critical error
        record_poller_metrics('exec-123', 'DRILL', waves)
    
    def test_record_metrics_counts_servers(self, mock_env, mock_clients):
        """Test metrics count server statuses."""
        waves = [
            {
                'Servers': [
                    {'Status': 'LAUNCHED'},
                    {'Status': 'LAUNCHED'},
                    {'Status': 'LAUNCHING'}
                ]
            }
        ]
        
        mock_clients['cloudwatch'].put_metric_data.return_value = {}
        
        record_poller_metrics('exec-123', 'DRILL', waves)
        
        # Verify metrics published with correct data
        call_args = mock_clients['cloudwatch'].put_metric_data.call_args[1]
        metrics = call_args['MetricData']
        
        assert len(metrics) == 2  # ActivePollingExecutions, WavesPolled
        assert metrics[0]['MetricName'] == 'ActivePollingExecutions'
        assert metrics[1]['MetricName'] == 'WavesPolled'

class TestFormatHelpers:
    """Tests for DynamoDB formatting helpers."""
    
    def test_format_wave_string(self):
        """Test formatting wave with string values."""
        wave = {'WaveId': 'wave-1', 'Status': 'COMPLETED'}
        
        formatted = format_wave_for_dynamodb(wave)
        
        assert formatted['M']['WaveId'] == {'S': 'wave-1'}
        assert formatted['M']['Status'] == {'S': 'COMPLETED'}
    
    def test_format_wave_number(self):
        """Test formatting wave with number values."""
        wave = {'WaveId': 'wave-1', 'Priority': 1, 'Delay': 30.5}
        
        formatted = format_wave_for_dynamodb(wave)
        
        assert formatted['M']['Priority'] == {'N': '1'}
        assert formatted['M']['Delay'] == {'N': '30.5'}
    
    def test_format_wave_boolean(self):
        """Test formatting wave with boolean values."""
        wave = {'WaveId': 'wave-1', 'Enabled': True}
        
        formatted = format_wave_for_dynamodb(wave)
        
        assert formatted['M']['Enabled'] == {'BOOL': True}
    
    def test_format_wave_list(self):
        """Test formatting wave with list values."""
        wave = {'WaveId': 'wave-1', 'Servers': ['server-1', 'server-2']}
        
        formatted = format_wave_for_dynamodb(wave)
        
        assert 'L' in formatted['M']['Servers']
        assert len(formatted['M']['Servers']['L']) == 2
    
    def test_format_wave_nested_dict(self):
        """Test formatting wave with nested dictionary."""
        wave = {
            'WaveId': 'wave-1',
            'Config': {'Region': 'us-east-1', 'Type': 'EC2'}
        }
        
        formatted = format_wave_for_dynamodb(wave)
        
        assert 'M' in formatted['M']['Config']
        assert formatted['M']['Config']['M']['Region'] == {'S': 'us-east-1'}
    
    def test_format_value_string(self):
        """Test formatting string value."""
        value = format_value_for_dynamodb('test-string')
        assert value == {'S': 'test-string'}
    
    def test_format_value_number(self):
        """Test formatting number value."""
        value = format_value_for_dynamodb(42)
        assert value == {'N': '42'}
    
    def test_format_value_boolean(self):
        """Test formatting boolean value."""
        value = format_value_for_dynamodb(True)
        assert value == {'BOOL': True}
    
    def test_format_value_list(self):
        """Test formatting list value."""
        value = format_value_for_dynamodb(['item1', 'item2'])
        assert value['L'][0] == {'S': 'item1'}
    
    def test_format_value_dict(self):
        """Test formatting dict value."""
        value = format_value_for_dynamodb({'key': 'value'})
        assert 'M' in value

class TestParseDynamoDBItem:
    """Tests for DynamoDB item parsing (same as execution_finder)."""
    
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
    
    def test_parse_number_float(self):
        """Test parsing float number attribute."""
        item = {'Price': {'N': '123.45'}}
        result = parse_dynamodb_item(item)
        assert result['Price'] == 123.45
    
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
        item = {'Tags': {'L': [{'S': 'tag1'}, {'S': 'tag2'}]}}
        result = parse_dynamodb_item(item)
        assert result['Tags'] == ['tag1', 'tag2']
    
    def test_parse_map(self):
        """Test parsing map attribute."""
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
        value = {'L': [{'S': 'item1'}, {'N': '123'}]}
        result = parse_dynamodb_value(value)
        assert result == ['item1', 123]

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
