# Design Document
# Execution Engine Testing

## Overview

The Execution Engine Testing specification defines a comprehensive testing strategy for the AWS DRS Orchestration system's core orchestration component. The Execution Engine, implemented as an AWS Step Functions state machine with orchestration Lambda functions (556 lines Python), currently has 0% test coverage despite being production-ready code.

This design establishes three testing layers:
1. **Unit Tests** - Fast, isolated tests with mocked AWS services
2. **Integration Tests** - Tests against real AWS services (DRS, DynamoDB, Step Functions)
3. **End-to-End Tests** - Complete recovery scenarios with real DRS servers

## Architecture

### Testing Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Test Orchestration                       │
│                        (pytest)                              │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────────┐    ┌──────────────┐
│  Unit Tests  │    │ Integration Tests│    │  E2E Tests   │
│              │    │                  │    │              │
│ • Mocked AWS │    │ • Real DRS API   │    │ • Real       │
│ • Fast (<1s) │    │ • Real DynamoDB  │    │   Servers    │
│ • Isolated   │    │ • Real Step Fns  │    │ • Full Flow  │
└──────────────┘    └──────────────────┘    └──────────────┘
        │                     │                     │
        └─────────────────────┴─────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Test Reports    │
                    │  • Coverage      │
                    │  • Performance   │
                    │  • Failures      │
                    └──────────────────┘
```

### Test Environment Configuration

**Unit Test Environment**:
- Mocked AWS services using `moto` library
- In-memory DynamoDB tables
- Synthetic test data
- No AWS credentials required

**Integration Test Environment**:
- AWS TEST account (438465159935)
- Region: us-east-1
- Real DynamoDB tables with `-test` suffix
- Real Step Functions state machine
- Mocked DRS API (to avoid costs)

**E2E Test Environment**:
- AWS TEST account with real DRS servers
- 6 Windows servers in CONTINUOUS replication
- Real recovery operations in drill mode
- Automatic cleanup after tests

## Components and Interfaces

### Test Framework Components

**1. Test Fixtures** (`tests/fixtures/`)
- `recovery_plan_fixtures.py` - Sample recovery plans with various wave configurations
- `drs_response_fixtures.py` - Mocked DRS API responses
- `execution_history_fixtures.py` - Sample execution history records

**2. Mock Services** (`tests/mocks/`)
- `mock_drs_client.py` - Mocked DRS API with realistic behavior
- `mock_step_functions.py` - Mocked Step Functions for unit tests
- `mock_dynamodb.py` - In-memory DynamoDB for fast tests

**3. Test Utilities** (`tests/utils/`)
- `test_data_generator.py` - Generate random test data
- `assertion_helpers.py` - Custom assertions for wave validation
- `cleanup_helpers.py` - Cleanup test resources after runs

**4. Integration Test Harness** (`tests/integration/`)
- `drs_integration_test.py` - DRS API integration tests
- `step_functions_integration_test.py` - State machine tests
- `dynamodb_integration_test.py` - Database persistence tests

**5. E2E Test Scenarios** (`tests/e2e/`)
- `basic_recovery_test.py` - Simple 1-wave recovery
- `multi_wave_recovery_test.py` - 3-wave with dependencies
- `parallel_recovery_test.py` - Parallel server launches
- `error_recovery_test.py` - Failure scenarios

## Data Models

### Test Data Schema

**Recovery Plan Test Data**:
```python
{
    "PlanId": "test-plan-001",
    "PlanName": "Test 3-Tier Application",
    "Waves": [
        {
            "WaveNumber": 1,
            "WaveName": "Database Tier",
            "ServerIds": ["s-test001", "s-test002"],
            "ExecutionType": "SEQUENTIAL",
            "ExecutionOrder": [1, 2],
            "Dependencies": [],
            "WaitTimeSeconds": 60
        }
    ]
}
```

**DRS Mock Response Schema**:
```python
{
    "job": {
        "jobID": "mock-job-001",
        "status": "COMPLETED",  # PENDING | IN_PROGRESS | COMPLETED | FAILED
        "initiatedBy": "TEST",
        "creationDateTime": "2025-11-19T10:00:00Z"
    }
}
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Wave Sequential Execution Order

*For any* recovery plan with N sequential waves, executing the plan should result in waves completing in order: Wave 1, then Wave 2, ..., then Wave N, with no wave starting before its predecessor completes.

**Validates: Requirements 1.1**

### Property 2: Wave Dependency Enforcement

*For any* wave W that depends on wave D, wave W should not start execution until wave D has status COMPLETED.

**Validates: Requirements 1.2**

### Property 3: Wait Time Compliance

*For any* wave with WaitTimeSeconds configured, the actual time between wave completion and next wave start should be within ±10% of the configured value.

**Validates: Requirements 1.3**

### Property 4: Parallel Launch Simultaneity

*For any* wave configured with ExecutionType=PARALLEL containing N servers, all N DRS StartRecovery API calls should occur within 5 seconds of each other.

**Validates: Requirements 1.4**

### Property 5: Sequential Launch Ordering

*For any* wave configured with ExecutionType=SEQUENTIAL with servers ordered [S1, S2, ..., SN], each server Si should start recovery only after server Si-1 reaches COMPLETED status.

**Validates: Requirements 1.5**

### Property 6: DRS API Parameter Correctness

*For any* server recovery operation, the DRS StartRecovery API call should include sourceServerID matching the server being recovered and recoverySnapshotID set to 'LATEST'.

**Validates: Requirements 2.1**

### Property 7: DRS Job Status Parsing

*For any* DRS job status response containing status field with value in {PENDING, IN_PROGRESS, COMPLETED, FAILED}, the Execution Engine should correctly parse and map the status to internal execution state.

**Validates: Requirements 2.3**

### Property 8: Throttling Retry Behavior

*For any* DRS API call that returns throttling error, the Execution Engine should retry up to 3 times with exponential backoff delays of 2^attempt seconds.

**Validates: Requirements 2.4**

### Property 9: Health Check Invocation

*For any* completed recovery job with instance ID I, the Execution Engine should call ec2.describe_instance_status with InstanceIds=[I] before marking recovery complete.

**Validates: Requirements 3.1**

### Property 10: Health Check Polling

*For any* instance in "pending" state, the Execution Engine should poll status every 30 seconds for up to 5 minutes (10 polls maximum) before timing out.

**Validates: Requirements 3.3**

### Property 11: Error Message Capture

*For any* DRS recovery job that fails, the execution history record should contain the error message from the DRS API response in the Errors field.

**Validates: Requirements 4.1**

### Property 12: Cascading Wave Failure

*For any* wave W that fails, all waves that depend on W (directly or transitively) should be marked with Status=SKIPPED without attempting execution.

**Validates: Requirements 4.2**

### Property 13: Network Error Retry

*For any* DRS API call that fails with network error, the Execution Engine should retry with exponential backoff (2^attempt seconds) up to 3 times before failing.

**Validates: Requirements 4.4**

### Property 14: Execution History Initialization

*For any* execution start, a DynamoDB record should be created with all required fields: ExecutionId (UUID), PlanId, Status=RUNNING, StartTime (Unix timestamp), and InitiatedBy.

**Validates: Requirements 5.1**

### Property 15: Wave Status Updates

*For any* wave completion, the execution history record should be updated with wave status, timing (StartTime, EndTime), and server results within 5 seconds of wave completion.

**Validates: Requirements 5.2**

### Property 16: Execution Finalization

*For any* execution that completes (successfully or with failure), the execution history record should have EndTime set and Status updated to either COMPLETED or FAILED.

**Validates: Requirements 5.3**

### Property 17: Server Error Detail Capture

*For any* server recovery that fails, the execution history should record the server ID, error message, and DRS job ID in the WaveStatus.ServerResults array.

**Validates: Requirements 5.4**

### Property 18: Execution History Schema Compliance

*For any* execution history record queried from DynamoDB, all required fields (ExecutionId, PlanId, Status, StartTime, InitiatedBy) should be non-null and correctly typed.

**Validates: Requirements 5.5**

### Property 19: Cross-Account Role Assumption

*For any* recovery plan with target account ID different from source account, the Execution Engine should call sts.assume_role with the cross-account role ARN before making DRS API calls.

**Validates: Requirements 6.1**

### Property 20: Assumed Credentials Usage

*For any* cross-account recovery, all DRS API calls should use temporary credentials from the assumed role, not the original Lambda execution role credentials.

**Validates: Requirements 6.2**

### Property 21: Credential Refresh on Expiration

*For any* execution lasting longer than 1 hour, if temporary credentials expire, the Execution Engine should automatically refresh credentials by re-assuming the role.

**Validates: Requirements 6.4**

### Property 22: Cross-Account Audit Trail

*For any* cross-account recovery, the execution history record should contain both SourceAccountId and TargetAccountId fields populated with correct account numbers.

**Validates: Requirements 6.5**

### Property 23: SNS Success Notification

*For any* execution that completes with Status=COMPLETED, an SNS message should be published containing ExecutionId, PlanId, Status, Duration, and ServerCount.

**Validates: Requirements 8.1**

### Property 24: SNS Failure Notification

*For any* execution that completes with Status=FAILED, an SNS message should be published containing error details and list of affected server IDs.

**Validates: Requirements 8.2**

### Property 25: SNS Message Content Completeness

*For any* SNS notification sent, the message body should contain all required fields: ExecutionId, PlanId, Status, Duration (in seconds), and ServerCount (integer).

**Validates: Requirements 8.5**

### Property 26: Lambda Retry Configuration

*For any* Lambda invocation failure in Step Functions, the state machine should retry up to 3 times with exponential backoff intervals of 2^attempt seconds.

**Validates: Requirements 9.1**

### Property 27: Execution Idempotency

*For any* recovery plan P, starting execution twice with the same parameters should return the same ExecutionId if the first execution is still running.

**Validates: Requirements 9.2**

### Property 28: DRS API Idempotency

*For any* DRS StartRecovery call that is retried, the DRS API should not create duplicate recovery jobs (verified by checking job count for the source server).

**Validates: Requirements 9.3**

### Property 29: DynamoDB Write Retry

*For any* DynamoDB write operation that fails with throttling or transient error, the Execution Engine should retry the write operation up to 3 times.

**Validates: Requirements 9.4**

### Property 30: DRS Response Schema Validation

*For any* DRS API response, the response structure should match the expected schema with required fields present and correctly typed.

**Validates: Requirements 10.5**


## Error Handling

### Error Categories

**1. DRS API Errors**
- Throttling (429) → Retry with exponential backoff
- Server not found (404) → Fail immediately with clear error
- Invalid parameters (400) → Fail immediately with validation error
- Service unavailable (503) → Retry up to 3 times

**2. Step Functions Errors**
- Lambda timeout → Retry with longer timeout
- State machine timeout → Fail execution with timeout reason
- Invalid state transition → Fail immediately (indicates bug)

**3. DynamoDB Errors**
- Throttling → Retry with exponential backoff
- Item not found → Return 404 to caller
- Conditional check failed → Return 409 conflict

**4. Network Errors**
- Connection timeout → Retry up to 3 times
- DNS resolution failure → Fail immediately
- SSL/TLS errors → Fail immediately (security issue)

### Error Recovery Strategies

**Transient Errors** (retry):
- DRS API throttling
- DynamoDB throttling
- Network timeouts
- Lambda cold starts

**Permanent Errors** (fail fast):
- Invalid server IDs
- Missing IAM permissions
- Invalid recovery plan configuration
- Circular wave dependencies

**Partial Failures** (continue with degradation):
- SNS notification failure → Log error, continue execution
- Health check timeout → Mark server as WARNING, continue
- Single server failure in parallel wave → Continue with remaining servers

## Testing Strategy

### Test Pyramid Distribution

**Target Coverage**:
- 70% Unit Tests (fast, isolated, mocked)
- 20% Integration Tests (real AWS services)
- 10% E2E Tests (complete scenarios)

### Unit Testing Approach

**Framework**: pytest with moto for AWS mocking

**Test Structure**:
```python
def test_wave_sequential_execution():
    """Property 1: Waves execute in order"""
    # Arrange
    plan = create_test_plan(waves=3, execution_type="SEQUENTIAL")
    mock_drs = MockDRSClient()
    
    # Act
    result = execute_recovery_plan(plan, drs_client=mock_drs)
    
    # Assert
    assert result.wave_order == [1, 2, 3]
    assert all(wave.start_time < next_wave.start_time 
               for wave, next_wave in zip(result.waves, result.waves[1:]))
```

**Mocking Strategy**:
- Mock all AWS SDK calls (boto3)
- Use realistic response data from fixtures
- Simulate timing delays for async operations
- Support both success and failure scenarios

### Integration Testing Approach

**Framework**: pytest with real AWS services in TEST account

**Test Structure**:
```python
@pytest.mark.integration
def test_drs_api_integration():
    """Validate DRS API calls with real service"""
    # Arrange
    drs_client = boto3.client('drs', region_name='us-east-1')
    test_server_id = "s-3d75cdc0d9a28a725"  # Real test server
    
    # Act
    response = drs_client.describe_source_servers(
        filters={'sourceServerIDs': [test_server_id]}
    )
    
    # Assert
    assert len(response['items']) == 1
    assert response['items'][0]['sourceServerID'] == test_server_id
    assert response['items'][0]['replicationStatus'] == 'CONTINUOUS'
```

**Integration Test Scope**:
- DRS API contract validation
- DynamoDB persistence operations
- Step Functions state transitions
- Cross-account IAM role assumption

### E2E Testing Approach

**Framework**: pytest with real DRS servers in drill mode

**Test Structure**:
```python
@pytest.mark.e2e
@pytest.mark.slow
def test_complete_3tier_recovery():
    """End-to-end test of 3-tier application recovery"""
    # Arrange
    plan = create_3tier_recovery_plan()
    
    # Act
    execution_id = start_recovery_execution(plan, execution_type="DRILL")
    result = wait_for_completion(execution_id, timeout=900)  # 15 min
    
    # Assert
    assert result.status == "COMPLETED"
    assert len(result.recovered_instances) == 6
    assert all(instance.state == "running" for instance in result.recovered_instances)
    
    # Cleanup
    terminate_drill_instances(result.recovered_instances)
```

**E2E Test Scenarios**:
1. Basic single-wave recovery (2 servers)
2. Multi-wave with dependencies (3 waves, 6 servers)
3. Parallel execution (4 servers simultaneously)
4. Error recovery (simulate server failure)
5. Cross-account recovery (if multi-account setup available)

### Property-Based Testing

**Framework**: Hypothesis for property-based testing

**Example Property Test**:
```python
from hypothesis import given, strategies as st

@given(
    wave_count=st.integers(min_value=1, max_value=10),
    servers_per_wave=st.integers(min_value=1, max_value=5)
)
def test_wave_execution_order_property(wave_count, servers_per_wave):
    """Property: Waves always execute in sequential order"""
    # Generate random recovery plan
    plan = generate_recovery_plan(
        waves=wave_count,
        servers_per_wave=servers_per_wave,
        execution_type="SEQUENTIAL"
    )
    
    # Execute with mocked DRS
    result = execute_with_mocks(plan)
    
    # Verify property holds
    wave_start_times = [w.start_time for w in result.waves]
    assert wave_start_times == sorted(wave_start_times)
```

**Properties to Test**:
- Wave execution order (Property 1)
- Dependency enforcement (Property 2)
- Parallel launch timing (Property 4)
- Error message capture (Property 11)
- Schema compliance (Property 18)

### Performance Testing

**Load Test Scenarios**:
1. **Small Load**: 6 servers, 3 waves → Target: < 5 minutes
2. **Medium Load**: 20 servers, 5 waves → Target: < 15 minutes
3. **Large Load**: 50 servers, 10 waves → Target: < 30 minutes

**Performance Metrics**:
- Wave initiation time (< 5 seconds)
- DRS API response time (< 2 seconds p95)
- Health check polling interval (30 seconds ±2 seconds)
- DynamoDB write latency (< 100ms p95)
- Step Functions state transition time (< 1 second)

**Performance Test Tools**:
- AWS CloudWatch for metrics collection
- Custom timing instrumentation in Lambda
- pytest-benchmark for unit test performance
- Locust for load testing (if API-driven)

### Test Data Management

**Test Data Sets**:

**1. Minimal Test Data** (unit tests):
```python
MINIMAL_PLAN = {
    "PlanId": "test-001",
    "Waves": [
        {"WaveNumber": 1, "ServerIds": ["s-test001"]}
    ]
}
```

**2. Standard Test Data** (integration tests):
```python
STANDARD_PLAN = {
    "PlanId": "test-002",
    "Waves": [
        {"WaveNumber": 1, "ServerIds": ["s-3d75cdc0d9a28a725", "s-3afa164776f93ce4f"]},
        {"WaveNumber": 2, "ServerIds": ["s-3c1730a9e0771ea14", "s-3c63bb8be30d7d071"]},
        {"WaveNumber": 3, "ServerIds": ["s-3578f52ef3bdd58b4", "s-3b9401c1cd270a7a8"]}
    ]
}
```

**3. Error Test Data** (negative tests):
```python
INVALID_PLAN = {
    "PlanId": "test-003",
    "Waves": [
        {"WaveNumber": 1, "ServerIds": ["s-invalid-id"]},  # Invalid server
        {"WaveNumber": 2, "ServerIds": [], "Dependencies": ["Wave-1"]}  # Empty wave
    ]
}
```

**Test Data Cleanup**:
- Automatic cleanup after each test using pytest fixtures
- Cleanup Lambda function for E2E tests
- DynamoDB table truncation for integration tests
- Drill instance termination after E2E tests

### Continuous Integration

**CI Pipeline** (GitHub Actions / AWS CodePipeline):

```yaml
name: Execution Engine Tests

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run unit tests
        run: pytest tests/unit/ -v --cov=lambda/orchestration
      - name: Upload coverage
        uses: codecov/codecov-action@v2
  
  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    steps:
      - uses: actions/checkout@v2
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v1
      - name: Run integration tests
        run: pytest tests/integration/ -v --aws-region=us-east-1
  
  e2e-tests:
    runs-on: ubuntu-latest
    needs: integration-tests
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v2
      - name: Run E2E tests
        run: pytest tests/e2e/ -v --slow
```

**Quality Gates**:
- Unit test coverage > 80%
- All integration tests passing
- E2E tests passing (on main branch only)
- No critical security vulnerabilities
- Performance benchmarks within targets

