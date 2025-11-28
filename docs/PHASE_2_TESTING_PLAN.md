# Phase 2: EventBridge Polling Service - Testing Plan

## Document Overview

**Purpose**: Comprehensive testing strategy for Phase 2 EventBridge polling service implementation  
**Scope**: Unit tests, integration tests, load tests, edge cases, monitoring validation  
**Target**: Zero production incidents, 99.9% completion detection accuracy  
**Created**: 2025-11-28  
**Status**: Ready for Implementation

## Testing Philosophy

**Core Principles:**
1. **Test behavior, not implementation** - Focus on outcomes, not internal logic
2. **Fail fast, fail loud** - Immediate feedback on regressions
3. **Production parity** - Test environment mirrors production
4. **Automated everything** - No manual test execution
5. **Observable failures** - Clear logs and metrics when tests fail

## Testing Layers

```
┌─────────────────────────────────────────────┐
│ Layer 4: Production Monitoring (Ongoing)   │
│ - CloudWatch Alarms                         │
│ - Real execution tracking                   │
└─────────────────────────────────────────────┘
           ↑
┌─────────────────────────────────────────────┐
│ Layer 3: Load Testing (Pre-deployment)     │
│ - 50 concurrent executions                  │
│ - Stress test: 100+ concurrent             │
│ - DynamoDB GSI performance validation       │
└─────────────────────────────────────────────┘
           ↑
┌─────────────────────────────────────────────┐
│ Layer 2: Integration Testing (CI/CD)       │
│ - End-to-end workflow validation            │
│ - Multi-wave execution tracking             │
│ - DRILL vs RECOVERY mode validation         │
│ - Timeout handling verification             │
└─────────────────────────────────────────────┘
           ↑
┌─────────────────────────────────────────────┐
│ Layer 1: Unit Testing (Developer)          │
│ - Adaptive polling logic                    │
│ - Phase detection algorithms                │
│ - Status transition validation              │
│ - Mock DRS API responses                    │
└─────────────────────────────────────────────┘
```

---

## Layer 1: Unit Testing

### 1.1 Execution Finder Lambda Tests

**File**: `tests/python/test_execution_finder.py`

#### Test Suite 1: GSI Query Logic

**Test 1.1.1: Query StatusIndex for POLLING executions**
```python
def test_query_status_index_polling():
    """Verify GSI query returns only POLLING executions"""
    
    # Setup: Create test executions with various statuses
    test_data = [
        {'ExecutionId': 'exec-1', 'Status': 'POLLING', 'StartTime': 1000},
        {'ExecutionId': 'exec-2', 'Status': 'COMPLETED', 'StartTime': 2000},
        {'ExecutionId': 'exec-3', 'Status': 'POLLING', 'StartTime': 3000},
        {'ExecutionId': 'exec-4', 'Status': 'FAILED', 'StartTime': 4000},
        {'ExecutionId': 'exec-5', 'Status': 'POLLING', 'StartTime': 5000},
    ]
    
    # Mock DynamoDB query response
    mock_response = {
        'Items': [
            test_data[0],  # POLLING
            test_data[2],  # POLLING
            test_data[4],  # POLLING
        ]
    }
    
    with patch('boto3.resource') as mock_dynamodb:
        mock_table = Mock()
        mock_table.query.return_value = mock_response
        mock_dynamodb.return_value.Table.return_value = mock_table
        
        # Execute
        result = find_polling_executions()
        
        # Assert
        assert len(result) == 3
        assert all(e['Status'] == 'POLLING' for e in result)
        
        # Verify GSI was used
        mock_table.query.assert_called_once()
        call_kwargs = mock_table.query.call_args[1]
        assert call_kwargs['IndexName'] == 'StatusIndex'
        assert 'Status' in str(call_kwargs['KeyConditionExpression'])
```

**Test 1.1.2: Handle empty result set**
```python
def test_query_status_index_no_polling_executions():
    """Verify graceful handling when no POLLING executions exist"""
    
    mock_response = {'Items': []}
    
    with patch('boto3.resource') as mock_dynamodb:
        mock_table = Mock()
        mock_table.query.return_value = mock_response
        mock_dynamodb.return_value.Table.return_value = mock_table
        
        result = find_polling_executions()
        
        assert result == []
        assert len(result) == 0
```

**Test 1.1.3: Handle DynamoDB errors**
```python
def test_query_status_index_dynamodb_error():
    """Verify error handling for DynamoDB failures"""
    
    with patch('boto3.resource') as mock_dynamodb:
        mock_table = Mock()
        mock_table.query.side_effect = ClientError(
            {'Error': {'Code': 'ProvisionedThroughputExceededException'}},
            'Query'
        )
        mock_dynamodb.return_value.Table.return_value = mock_table
        
        with pytest.raises(Exception) as exc_info:
            find_polling_executions()
        
        assert 'DynamoDB' in str(exc_info.value)
```

#### Test Suite 2: Adaptive Polling Logic

**Test 1.2.1: PENDING phase requires 45-second interval**
```python
def test_adaptive_polling_pending_phase():
    """Verify 45-second interval during PENDING phase"""
    
    execution = {
        'ExecutionId': 'exec-1',
        'LastPolledTime': int(time.time()) - 40,  # 40 seconds ago
        'Waves': [{
            'Servers': [
                {'Status': 'PENDING'},
                {'Status': 'PENDING'},
            ]
        }]
    }
    
    # Should NOT poll yet (need 45 seconds)
    assert should_poll_now(execution) == False
    
    # Move time forward 10 seconds
    execution['LastPolledTime'] = int(time.time()) - 50
    
    # Should poll now (50 > 45)
    assert should_poll_now(execution) == True
```

**Test 1.2.2: STARTED phase requires 15-second interval**
```python
def test_adaptive_polling_started_phase():
    """Verify 15-second interval during critical STARTED transition"""
    
    execution = {
        'ExecutionId': 'exec-1',
        'LastPolledTime': int(time.time()) - 12,  # 12 seconds ago
        'Waves': [{
            'Servers': [
                {'Status': 'STARTED'},  # Critical transition
                {'Status': 'PENDING'},
            ]
        }]
    }
    
    # Should NOT poll yet (need 15 seconds)
    assert should_poll_now(execution) == False
    
    # Move time forward 5 seconds
    execution['LastPolledTime'] = int(time.time()) - 17
    
    # Should poll now (17 > 15)
    assert should_poll_now(execution) == True
```

**Test 1.2.3: IN_PROGRESS phase requires 30-second interval**
```python
def test_adaptive_polling_in_progress_phase():
    """Verify 30-second interval during normal IN_PROGRESS phase"""
    
    execution = {
        'ExecutionId': 'exec-1',
        'LastPolledTime': int(time.time()) - 25,  # 25 seconds ago
        'Waves': [{
            'Servers': [
                {'Status': 'IN_PROGRESS'},
                {'Status': 'IN_PROGRESS'},
            ]
        }]
    }
    
    # Should NOT poll yet (need 30 seconds)
    assert should_poll_now(execution) == False
    
    # Move time forward 10 seconds
    execution['LastPolledTime'] = int(time.time()) - 35
    
    # Should poll now (35 > 30)
    assert should_poll_now(execution) == True
```

**Test 1.2.4: Phase detection accuracy**
```python
def test_detect_execution_phase():
    """Verify correct phase detection from wave statuses"""
    
    # All PENDING
    waves = [{'Servers': [{'Status': 'PENDING'}, {'Status': 'PENDING'}]}]
    assert detect_execution_phase(waves) == 'PENDING'
    
    # Mixed with STARTED (highest priority)
    waves = [{'Servers': [{'Status': 'STARTED'}, {'Status': 'PENDING'}]}]
    assert detect_execution_phase(waves) == 'STARTED'
    
    # All IN_PROGRESS
    waves = [{'Servers': [{'Status': 'IN_PROGRESS'}, {'Status': 'IN_PROGRESS'}]}]
    assert detect_execution_phase(waves) == 'IN_PROGRESS'
    
    # Mixed phases
    waves = [
        {'Servers': [{'Status': 'COMPLETED'}]},
        {'Servers': [{'Status': 'LAUNCHING'}]}
    ]
    assert detect_execution_phase(waves) == 'LAUNCHING'
```

#### Test Suite 3: Lambda Invocation Logic

**Test 1.3.1: Invoke poller per execution**
```python
def test_invoke_poller_per_execution():
    """Verify separate poller invocation for each execution"""
    
    executions = [
        {'ExecutionId': 'exec-1', 'PlanId': 'plan-1'},
        {'ExecutionId': 'exec-2', 'PlanId': 'plan-2'},
        {'ExecutionId': 'exec-3', 'PlanId': 'plan-3'},
    ]
    
    with patch('boto3.client') as mock_lambda:
        mock_client = Mock()
        mock_lambda.return_value = mock_client
        
        invoke_pollers_for_executions(executions)
        
        # Verify 3 separate invocations
        assert mock_client.invoke.call_count == 3
        
        # Verify async invocation type
        for call in mock_client.invoke.call_args_list:
            kwargs = call[1]
            assert kwargs['InvocationType'] == 'Event'
```

**Test 1.3.2: Handle Lambda invocation errors**
```python
def test_invoke_poller_error_handling():
    """Verify graceful error handling for Lambda invocation failures"""
    
    executions = [
        {'ExecutionId': 'exec-1', 'PlanId': 'plan-1'},
        {'ExecutionId': 'exec-2', 'PlanId': 'plan-2'},  # Will fail
        {'ExecutionId': 'exec-3', 'PlanId': 'plan-3'},
    ]
    
    with patch('boto3.client') as mock_lambda:
        mock_client = Mock()
        
        # First invocation succeeds, second fails, third succeeds
        mock_client.invoke.side_effect = [
            {'StatusCode': 202},
            ClientError({'Error': {'Code': 'TooManyRequestsException'}}, 'Invoke'),
            {'StatusCode': 202},
        ]
        
        mock_lambda.return_value = mock_client
        
        # Should continue despite error
        result = invoke_pollers_for_executions(executions)
        
        assert result['successful'] == 2
        assert result['failed'] == 1
```

---

### 1.2 Execution Poller Lambda Tests

**File**: `tests/python/test_execution_poller.py`

#### Test Suite 4: Wave Status Polling

**Test 1.4.1: Poll wave with all servers PENDING**
```python
def test_poll_wave_all_pending():
    """Verify wave polling when all servers still PENDING"""
    
    wave = {
        'WaveName': 'Wave-1',
        'Region': 'us-east-1',
        'Status': 'LAUNCHING',
        'Servers': [
            {'SourceServerId': 's-1', 'RecoveryJobId': 'job-1', 'Status': 'LAUNCHING'},
            {'SourceServerId': 's-2', 'RecoveryJobId': 'job-2', 'Status': 'LAUNCHING'},
        ]
    }
    
    # Mock DRS response - jobs still pending
    mock_drs_response = {
        'items': [
            {'jobID': 'job-1', 'status': 'PENDING'},
            {'jobID': 'job-2', 'status': 'PENDING'},
        ]
    }
    
    with patch('boto3.client') as mock_boto:
        mock_drs = Mock()
        mock_drs.describe_jobs.return_value = mock_drs_response
        mock_boto.return_value = mock_drs
        
        updated_wave = poll_wave_status(wave, 'DRILL')
        
        # Wave should still be LAUNCHING
        assert updated_wave['Status'] == 'LAUNCHING'
        
        # Servers should be PENDING
        assert all(s['Status'] == 'PENDING' for s in updated_wave['Servers'])
```

**Test 1.4.2: Poll wave with servers transitioning to STARTED**
```python
def test_poll_wave_transition_to_started():
    """Verify wave polling during critical STARTED transition"""
    
    wave = {
        'WaveName': 'Wave-1',
        'Region': 'us-east-1',
        'Status': 'LAUNCHING',
        'Servers': [
            {'SourceServerId': 's-1', 'RecoveryJobId': 'job-1', 'Status': 'PENDING'},
            {'SourceServerId': 's-2', 'RecoveryJobId': 'job-2', 'Status': 'PENDING'},
        ]
    }
    
    # Mock DRS response - jobs started
    mock_drs_response = {
        'items': [
            {'jobID': 'job-1', 'status': 'STARTED'},
            {'jobID': 'job-2', 'status': 'STARTED'},
        ]
    }
    
    with patch('boto3.client') as mock_boto:
        mock_drs = Mock()
        mock_drs.describe_jobs.return_value = mock_drs_response
        mock_boto.return_value = mock_drs
        
        updated_wave = poll_wave_status(wave, 'DRILL')
        
        # Servers should be STARTED
        assert all(s['Status'] == 'STARTED' for s in updated_wave['Servers'])
        
        # LastPolledTime should be updated
        assert all('LastPolledTime' in s for s in updated_wave['Servers'])
        
        # PollAttempts should be incremented
        assert all(s['PollAttempts'] == 1 for s in updated_wave['Servers'])
```

**Test 1.4.3: Poll wave with all servers COMPLETED (DRILL mode)**
```python
def test_poll_wave_drill_completion():
    """Verify DRILL mode completion when all servers LAUNCHED"""
    
    wave = {
        'WaveName': 'Wave-1',
        'Region': 'us-east-1',
        'Status': 'LAUNCHING',
        'ExecutionMode': 'DRILL',
        'Servers': [
            {'SourceServerId': 's-1', 'RecoveryJobId': 'job-1', 'Status': 'IN_PROGRESS'},
            {'SourceServerId': 's-2', 'RecoveryJobId': 'job-2', 'Status': 'IN_PROGRESS'},
        ]
    }
    
    # Mock DRS response - jobs completed with instance IDs
    mock_drs_response = {
        'items': [
            {
                'jobID': 'job-1',
                'status': 'COMPLETED',
                'participatingServers': [{
                    'sourceServerID': 's-1',
                    'recoveryInstanceID': 'i-abc123'
                }]
            },
            {
                'jobID': 'job-2',
                'status': 'COMPLETED',
                'participatingServers': [{
                    'sourceServerID': 's-2',
                    'recoveryInstanceID': 'i-def456'
                }]
            },
        ]
    }
    
    with patch('boto3.client') as mock_boto:
        mock_drs = Mock()
        mock_drs.describe_jobs.return_value = mock_drs_response
        mock_boto.return_value = mock_drs
        
        updated_wave = poll_wave_status(wave, 'DRILL')
        
        # Wave should be COMPLETED (DRILL doesn't wait for post-launch)
        assert updated_wave['Status'] == 'COMPLETED'
        
        # Servers should be LAUNCHED
        assert all(s['Status'] == 'LAUNCHED' for s in updated_wave['Servers'])
        
        # Instance IDs should be populated
        assert updated_wave['Servers'][0]['InstanceId'] == 'i-abc123'
        assert updated_wave['Servers'][1]['InstanceId'] == 'i-def456'
        
        # LaunchedTime should be set
        assert all('LaunchedTime' in s for s in updated_wave['Servers'])
```

**Test 1.4.4: Poll wave with RECOVERY mode post-launch actions**
```python
def test_poll_wave_recovery_post_launch():
    """Verify RECOVERY mode waits for post-launch actions"""
    
    wave = {
        'WaveName': 'Wave-1',
        'Region': 'us-east-1',
        'Status': 'LAUNCHING',
        'ExecutionMode': 'RECOVERY',
        'Servers': [
            {'SourceServerId': 's-1', 'RecoveryJobId': 'job-1', 'Status': 'IN_PROGRESS'},
        ]
    }
    
    # Mock DRS response - job completed but post-launch in progress
    mock_drs_response = {
        'items': [{
            'jobID': 'job-1',
            'status': 'COMPLETED',
            'participatingServers': [{
                'sourceServerID': 's-1',
                'recoveryInstanceID': 'i-abc123',
                'postLaunchActionsDeployment': {
                    'status': 'IN_PROGRESS'  # Still running SSM
                }
            }]
        }]
    }
    
    with patch('boto3.client') as mock_boto:
        mock_drs = Mock()
        mock_drs.describe_jobs.return_value = mock_drs_response
        mock_boto.return_value = mock_drs
        
        updated_wave = poll_wave_status(wave, 'RECOVERY')
        
        # Wave should NOT be complete yet
        assert updated_wave['Status'] != 'COMPLETED'
        
        # Server should be LAUNCHED but post-launch not complete
        assert updated_wave['Servers'][0]['Status'] == 'LAUNCHED'
        assert updated_wave['Servers'][0]['PostLaunchActionsStatus'] == 'IN_PROGRESS'
        
        # Now simulate post-launch completion
        mock_drs_response['items'][0]['participatingServers'][0]['postLaunchActionsDeployment']['status'] = 'COMPLETED'
        
        updated_wave = poll_wave_status(wave, 'RECOVERY')
        
        # NOW wave should be complete
        assert updated_wave['Status'] == 'COMPLETED'
        assert updated_wave['Servers'][0]['PostLaunchActionsStatus'] == 'COMPLETED'
```

#### Test Suite 5: Timeout Handling

**Test 1.5.1: Handle 30-minute timeout with DRS query**
```python
def test_timeout_handling_query_drs():
    """Verify timeout queries DRS for final status"""
    
    execution = {
        'ExecutionId': 'exec-1',
        'PlanId': 'plan-1',
        'StartTime': int(time.time()) - 1850,  # 30 min 50 sec ago
        'Waves': [{
            'Region': 'us-east-1',
            'Servers': [
                {'SourceServerId': 's-1', 'RecoveryJobId': 'job-1', 'Status': 'IN_PROGRESS'},
            ]
        }]
    }
    
    # Mock DRS final status query
    mock_drs_response = {
        'items': [{
            'jobID': 'job-1',
            'status': 'COMPLETED',  # Actually completed, just took longer than expected
            'participatingServers': [{
                'sourceServerID': 's-1',
                'recoveryInstanceID': 'i-abc123'
            }]
        }]
    }
    
    with patch('boto3.client') as mock_boto:
        mock_drs = Mock()
        mock_drs.describe_jobs.return_value = mock_drs_response
        mock_boto.return_value = mock_drs
        
        # Should detect timeout
        assert is_timed_out(execution) == True
        
        # Handle timeout
        handle_timeout('exec-1', 'plan-1', execution)
        
        # Should query DRS for truth
        mock_drs.describe_jobs.assert_called()
        
        # Should update with DRS truth, not fail arbitrarily
        assert execution['Waves'][0]['Servers'][0]['Status'] == 'COMPLETED'
        assert execution['Waves'][0]['Servers'][0]['TimeoutDetected'] == True
```

**Test 1.5.2: Timeout with DRS job still running**
```python
def test_timeout_handling_job_still_running():
    """Verify timeout preserves DRS status when job legitimately slow"""
    
    execution = {
        'ExecutionId': 'exec-1',
        'PlanId': 'plan-1',
        'StartTime': int(time.time()) - 1900,  # 31 min 40 sec ago
        'Waves': [{
            'Region': 'us-east-1',
            'Servers': [
                {'SourceServerId': 's-1', 'RecoveryJobId': 'job-1', 'Status': 'IN_PROGRESS'},
            ]
        }]
    }
    
    # Mock DRS - job still IN_PROGRESS (legitimately slow)
    mock_drs_response = {
        'items': [{
            'jobID': 'job-1',
            'status': 'IN_PROGRESS',  # Still running after 30 min
        }]
    }
    
    with patch('boto3.client') as mock_boto:
        mock_drs = Mock()
        mock_drs.describe_jobs.return_value = mock_drs_response
        mock_boto.return_value = mock_drs
        
        handle_timeout('exec-1', 'plan-1', execution)
        
        # Should preserve DRS status
        assert execution['Waves'][0]['Servers'][0]['Status'] == 'IN_PROGRESS'
        
        # Should mark timeout but not fail
        assert execution['Waves'][0]['Servers'][0]['TimeoutDetected'] == True
        
        # Execution status should be TIMEOUT, not FAILED
        # (allows manual investigation)
```

---

## Layer 2: Integration Testing

### 2.1 End-to-End Workflow Tests

**File**: `tests/integration/test_polling_workflow.py`

#### Test Suite 6: Single Execution Workflow

**Test 2.1.1: Complete DRILL execution end-to-end**
```python
@pytest.mark.integration
@pytest.mark.slow
def test_drill_execution_complete_workflow():
    """
    Full integration test: API request → polling → completion
    Duration: ~3 minutes (fast-forwarded with mocks)
    """
    
    # Step 1: Create execution via API
    response = requests.post(
        f"{API_URL}/executions",
        json={
            'PlanId': 'test-plan-1',
            'ExecutionType': 'DRILL'
        }
    )
    
    assert response.status_code == 202
    execution_id = response.json()['executionId']
    
    # Step 2: Verify execution in PENDING status
    execution = get_execution_from_dynamodb(execution_id)
    assert execution['Status'] == 'PENDING'
    
    # Step 3: Mock DRS jobs to transition through phases
    with mock_drs_progression():
        # Wait for worker to initiate jobs (max 2 min)
        wait_for_status(execution_id, 'POLLING', timeout=120)
        
        # Verify StatusIndex GSI query works
        polling_executions = query_status_index('POLLING')
        assert execution_id in [e['ExecutionId'] for e in polling_executions]
        
        # Step 4: Simulate DRS progression
        # PENDING → STARTED → IN_PROGRESS → COMPLETED
        
        # Phase 1: PENDING (13 minutes simulated)
        time.sleep(2)  # Wait for first poll
        execution = get_execution_from_dynamodb(execution_id)
        assert all(
            s['Status'] == 'PENDING'
            for w in execution['Waves']
            for s in w['Servers']
        )
        
        # Phase 2: STARTED transition (rapid polling expected)
        advance_drs_phase('STARTED')
        time.sleep(1)  # Rapid poll should catch this
        execution = get_execution_from_dynamodb(execution_id)
        assert any(
            s['Status'] == 'STARTED'
            for w in execution['Waves']
            for s in w['Servers']
        )
        
        # Phase 3: IN_PROGRESS (6 minutes simulated)
        advance_drs_phase('IN_PROGRESS')
        time.sleep(2)
        execution = get_execution_from_dynamodb(execution_id)
        assert all(
            s['Status'] == 'IN_PROGRESS'
            for w in execution['Waves']
            for s in w['Servers']
        )
        
        # Phase 4: COMPLETED
        advance_drs_phase('COMPLETED')
        
        # Wait for poller to detect completion
        wait_for_status(execution_id, 'COMPLETED', timeout=60)
        
        # Step 5: Verify final state
        execution = get_execution_from_dynamodb(execution_id)
        
        assert execution['Status'] == 'COMPLETED'
        assert execution['EndTime'] is not None
        assert all(
            s['Status'] == 'LAUNCHED'
            for w in execution['Waves']
            for s in w['Servers']
        )
        assert all(
            'InstanceId' in s and s['InstanceId'].startswith('i-')
            for w in execution['Waves']
            for s in w['Servers']
        )
        
        # Verify execution no longer in StatusIndex POLLING
        polling_executions = query_status_index('POLLING')
        assert execution_id not in [e['ExecutionId'] for e in polling_executions]
```

**Test 2.1.2: RECOVERY execution with post-launch actions**
```python
@pytest.mark.integration
@pytest.mark.slow
def test_recovery_execution_with_post_launch():
    """
    Integration test: RECOVERY mode with SSM post-launch actions
    Duration: ~5 minutes (fast-forwarded)
    """
    
    # Create RECOVERY execution
    response = requests.post(
        f"{API_URL}/executions",
        json={
            'PlanId': 'test-plan-1',
            'ExecutionType': 'RECOVERY'
        }
    )
    
    execution_id = response.json()['executionId']
    
    with mock_drs_progression():
        # Progress through phases
        wait_for_status(execution_id, 'POLLING', timeout=120)
        
        # Advance to COMPLETED (instances launched)
        advance_drs_phase('COMPLETED')
        time.sleep(3)
        
        execution = get_execution_from_dynamodb(execution_id)
        
        # Servers should be LAUNCHED but execution NOT complete
        assert all(
            s['Status'] == 'LAUNCHED'
            for w in execution['Waves']
            for s in w['Servers']
        )
        assert execution['Status'] == 'POLLING'  # Still polling for post-launch
        
        # Verify post-launch actions tracked
        assert all(
            'PostLaunchActionsStatus' in s
            for w in execution['Waves']
            for s in w['Servers']
        )
        
        # Simulate post-launch completion
        advance_post_launch_phase('COMPLETED')
        
        # Wait for completion detection
        wait_for_status(execution_id, 'COMPLETED', timeout=120)
        
        execution = get_execution_from_dynamodb(execution_id)
        
        # NOW execution should be complete
        assert execution['Status'] == 'COMPLETED'
        assert all(
            s['PostLaunchActionsStatus'] == 'COMPLETED'
            for w in execution['Waves']
            for s in w['Servers']
        )
```

#### Test Suite 7: Multi-Wave Execution

**Test 2.2.1: Sequential wave execution**
```python
@pytest.mark.integration
def test_multi_wave_sequential_execution():
    """Test execution with 3 waves in sequence"""
    
    plan = create_test_plan_with_waves(num_waves=3)
    
    response = requests.post(
        f"{API_URL}/executions",
        json={'PlanId': plan['PlanId'], 'ExecutionType': 'DRILL'}
    )
    
    execution_id = response.json()['executionId']
    
    with mock_drs_progression():
        wait_for_status(execution_id, 'POLLING', timeout=120)
        
        # All waves should be initiated (parallel start)
        execution = get_execution_from_dynamodb(execution_id)
        assert len(execution['Waves']) == 3
        assert all(w['Status'] == 'LAUNCHING' for w in execution['Waves'])
        
        # Complete all waves
        advance_drs_phase('COMPLETED')
        wait_for_status(execution_id, 'COMPLETED', timeout=180)
        
        execution = get_execution_from_dynamodb(execution_id)
        assert all(w['Status'] == 'COMPLETED' for w in execution['Waves'])
```

---

### 2.3 Edge Case Testing

#### Test Suite 8: Error Scenarios

**Test 2.3.1: Handle partial wave failure**
```python
@pytest.mark.integration
def test_partial_wave_failure():
    """Test execution when some servers fail"""
    
    response =
