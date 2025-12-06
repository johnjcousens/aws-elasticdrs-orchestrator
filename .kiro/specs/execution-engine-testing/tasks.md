# Implementation Plan
# Execution Engine Testing

- [x] 1. Set up test infrastructure and framework
  - Install pytest, moto, hypothesis, pytest-cov dependencies
  - Create test directory structure (unit/, integration/, e2e/, fixtures/, mocks/, utils/)
  - Configure pytest.ini with markers (unit, integration, e2e, slow)
  - Set up AWS credentials for integration tests
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

- [x] 2. Create test fixtures and mock services
  - [x] 2.1 Implement recovery plan fixtures
    - Create fixtures for 1-wave, 3-wave, and 5-wave plans
    - Include sequential, parallel, and mixed execution types
    - Add fixtures with wave dependencies
    - _Requirements: 12.1, 12.2_

  - [x] 2.2 Implement DRS mock client
    - Mock describe_source_servers with realistic responses
    - Mock start_recovery with job ID generation
    - Mock describe_jobs with status transitions (PENDING → IN_PROGRESS → COMPLETED)
    - Support throttling and error simulation
    - _Requirements: 11.1, 11.2, 11.3_

  - [x] 2.3 Implement test data generators
    - Random recovery plan generator with configurable waves
    - Random server ID generator (s-{17 hex chars} format)
    - Execution history generator for database seeding
    - _Requirements: 12.1, 12.2, 12.3_

- [ ] 3. Implement unit tests for wave orchestration
  - [ ] 3.1 Write property test for sequential wave execution
    - **Property 1: Wave Sequential Execution Order**
    - **Validates: Requirements 1.1**
    - Generate random plans with N waves
    - Verify waves execute in order 1, 2, ..., N
    - Assert each wave starts only after previous completes

  - [ ] 3.2 Write property test for wave dependencies
    - **Property 2: Wave Dependency Enforcement**
    - **Validates: Requirements 1.2**
    - Generate plans with dependency chains
    - Verify dependent waves wait for prerequisites
    - Test transitive dependencies (Wave 3 depends on Wave 2 depends on Wave 1)

  - [ ] 3.3 Write property test for wait time compliance
    - **Property 3: Wait Time Compliance**
    - **Validates: Requirements 1.3**
    - Generate waves with random WaitTimeSeconds (0-300)
    - Measure actual delay between waves
    - Assert delay within ±10% of configured value

  - [ ] 3.4 Write property test for parallel execution
    - **Property 4: Parallel Launch Simultaneity**
    - **Validates: Requirements 1.4**
    - Generate waves with multiple servers
    - Verify all DRS API calls occur within 5 seconds
    - Check concurrent execution using timestamps

  - [ ] 3.5 Write property test for sequential execution
    - **Property 5: Sequential Launch Ordering**
    - **Validates: Requirements 1.5**
    - Generate waves with ExecutionOrder specified
    - Verify servers launch one at a time in order
    - Assert Si+1 starts only after Si completes

- [ ] 4. Implement unit tests for DRS API integration
  - [ ] 4.1 Write property test for DRS API parameters
    - **Property 6: DRS API Parameter Correctness**
    - **Validates: Requirements 2.1**
    - Verify sourceServerID matches server being recovered
    - Verify recoverySnapshotID is 'LATEST'
    - Check isDrill flag matches execution type

  - [ ] 4.2 Write property test for job status parsing
    - **Property 7: DRS Job Status Parsing**
    - **Validates: Requirements 2.3**
    - Test all status values: PENDING, IN_PROGRESS, COMPLETED, FAILED
    - Verify correct mapping to internal states
    - Test unknown status handling

  - [ ] 4.3 Write property test for throttling retry
    - **Property 8: Throttling Retry Behavior**
    - **Validates: Requirements 2.4**
    - Simulate DRS throttling errors
    - Verify 3 retry attempts with exponential backoff
    - Assert backoff delays: 2s, 4s, 8s

  - [ ]* 4.4 Write unit test for drill mode flag
    - Verify isDrill=True passed when execution type is DRILL
    - Verify isDrill=False for RECOVERY type
    - _Requirements: 2.2_

  - [ ]* 4.5 Write unit test for missing server error
    - Test with invalid server ID
    - Verify error message contains server ID
    - _Requirements: 2.5_

- [ ] 5. Implement unit tests for health checks
  - [ ] 5.1 Write property test for health check invocation
    - **Property 9: Health Check Invocation**
    - **Validates: Requirements 3.1**
    - Verify EC2 API called for each recovered instance
    - Check correct instance IDs passed
    - Test health check skipping when disabled

  - [ ] 5.2 Write property test for health check polling
    - **Property 10: Health Check Polling**
    - **Validates: Requirements 3.3**
    - Simulate pending instance status
    - Verify 30-second polling interval
    - Assert 10 polls maximum (5 minutes)

  - [ ]* 5.3 Write unit test for running instance success
    - Mock instance status as "running"
    - Verify server marked as successfully recovered
    - _Requirements: 3.2_

  - [ ]* 5.4 Write unit test for health check timeout
    - Mock instance never reaching "running"
    - Verify recovery marked as FAILED after 5 minutes
    - _Requirements: 3.4_

  - [ ]* 5.5 Write unit test for health check disabled
    - Configure wave with health checks disabled
    - Verify no EC2 API calls made
    - _Requirements: 3.5_

- [ ] 6. Implement unit tests for error handling
  - [ ] 6.1 Write property test for error message capture
    - **Property 11: Error Message Capture**
    - **Validates: Requirements 4.1**
    - Simulate DRS job failures
    - Verify error messages stored in execution history
    - Check error details include job ID and server ID

  - [ ] 6.2 Write property test for cascading wave failure
    - **Property 12: Cascading Wave Failure**
    - **Validates: Requirements 4.2**
    - Fail early wave in dependency chain
    - Verify dependent waves marked SKIPPED
    - Test transitive dependency skipping

  - [ ] 6.3 Write property test for network error retry
    - **Property 13: Network Error Retry**
    - **Validates: Requirements 4.4**
    - Simulate network connection errors
    - Verify exponential backoff retry (2s, 4s, 8s)
    - Assert 3 retry attempts before failure

  - [ ]* 6.4 Write unit test for Step Functions timeout
    - Simulate long-running execution
    - Verify timeout triggers FAILED status
    - _Requirements: 4.3_

  - [ ]* 6.5 Write unit test for execution cancellation
    - Trigger cancellation during execution
    - Verify graceful shutdown
    - Check status marked as CANCELLED
    - _Requirements: 4.5_

- [ ] 7. Implement unit tests for execution history
  - [ ] 7.1 Write property test for execution initialization
    - **Property 14: Execution History Initialization**
    - **Validates: Requirements 5.1**
    - Start random executions
    - Verify DynamoDB records created with all required fields
    - Check ExecutionId is valid UUID, Status is RUNNING

  - [ ] 7.2 Write property test for wave status updates
    - **Property 15: Wave Status Updates**
    - **Validates: Requirements 5.2**
    - Complete waves with various outcomes
    - Verify updates applied within 5 seconds
    - Check wave timing and server results recorded

  - [ ] 7.3 Write property test for execution finalization
    - **Property 16: Execution Finalization**
    - **Validates: Requirements 5.3**
    - Complete executions (success and failure)
    - Verify EndTime set and Status updated
    - Assert final status is COMPLETED or FAILED

  - [ ] 7.4 Write property test for server error details
    - **Property 17: Server Error Detail Capture**
    - **Validates: Requirements 5.4**
    - Fail individual server recoveries
    - Verify server ID, error message, job ID recorded
    - Check details in WaveStatus.ServerResults

  - [ ] 7.5 Write property test for schema compliance
    - **Property 18: Execution History Schema Compliance**
    - **Validates: Requirements 5.5**
    - Query execution history records
    - Verify all required fields non-null
    - Check field types match schema

- [ ] 8. Implement unit tests for cross-account operations
  - [ ] 8.1 Write property test for role assumption
    - **Property 19: Cross-Account Role Assumption**
    - **Validates: Requirements 6.1**
    - Configure cross-account scenarios
    - Verify STS AssumeRole called with correct role ARN
    - Check role assumption before DRS API calls

  - [ ] 8.2 Write property test for assumed credentials usage
    - **Property 20: Assumed Credentials Usage**
    - **Validates: Requirements 6.2**
    - Verify DRS API calls use temporary credentials
    - Check credentials from assumed role, not Lambda role

  - [ ] 8.3 Write property test for credential refresh
    - **Property 21: Credential Refresh on Expiration**
    - **Validates: Requirements 6.4**
    - Simulate long-running execution (>1 hour)
    - Trigger credential expiration
    - Verify automatic role re-assumption

  - [ ] 8.4 Write property test for cross-account audit trail
    - **Property 22: Cross-Account Audit Trail**
    - **Validates: Requirements 6.5**
    - Perform cross-account recoveries
    - Verify both SourceAccountId and TargetAccountId recorded
    - Check account IDs are correct 12-digit numbers

  - [ ]* 8.5 Write unit test for role assumption failure
    - Simulate IAM permission denied
    - Verify error message includes role ARN and reason
    - _Requirements: 6.3_

- [ ] 9. Implement unit tests for notifications
  - [ ] 9.1 Write property test for success notifications
    - **Property 23: SNS Success Notification**
    - **Validates: Requirements 8.1**
    - Complete executions successfully
    - Verify SNS message published
    - Check message contains ExecutionId, PlanId, Status, Duration, ServerCount

  - [ ] 9.2 Write property test for failure notifications
    - **Property 24: SNS Failure Notification**
    - **Validates: Requirements 8.2**
    - Fail executions with errors
    - Verify SNS message includes error details
    - Check affected server IDs listed

  - [ ] 9.3 Write property test for notification content
    - **Property 25: SNS Message Content Completeness**
    - **Validates: Requirements 8.5**
    - Send various notifications
    - Verify all required fields present
    - Check field types and formats

  - [ ]* 9.4 Write unit test for missing SNS topic
    - Configure execution without SNS topic ARN
    - Verify execution continues without notification
    - _Requirements: 8.3_

  - [ ]* 9.5 Write unit test for SNS publish failure
    - Simulate SNS API error
    - Verify error logged but execution continues
    - _Requirements: 8.4_

- [ ] 10. Implement unit tests for idempotency
  - [ ] 10.1 Write property test for Lambda retry
    - **Property 26: Lambda Retry Configuration**
    - **Validates: Requirements 9.1**
    - Simulate Lambda failures
    - Verify 3 retry attempts
    - Check exponential backoff timing

  - [ ] 10.2 Write property test for execution idempotency
    - **Property 27: Execution Idempotency**
    - **Validates: Requirements 9.2**
    - Start same execution twice
    - Verify duplicate detection
    - Check same ExecutionId returned

  - [ ] 10.3 Write property test for DRS API idempotency
    - **Property 28: DRS API Idempotency**
    - **Validates: Requirements 9.3**
    - Retry DRS StartRecovery calls
    - Verify no duplicate jobs created
    - Check job count for server

  - [ ] 10.4 Write property test for DynamoDB retry
    - **Property 29: DynamoDB Write Retry**
    - **Validates: Requirements 9.4**
    - Simulate DynamoDB throttling
    - Verify write retries up to 3 times
    - Check exponential backoff

  - [ ]* 10.5 Write unit test for retry exhaustion
    - Exhaust all retry attempts
    - Verify clear error message
    - _Requirements: 9.5_

- [ ] 11. Checkpoint - Ensure all unit tests pass
  - Run full unit test suite: `pytest tests/unit/ -v`
  - Verify test coverage > 80%
  - Fix any failing tests
  - Ask user if questions arise

- [ ] 12. Implement integration tests
  - [ ] 12.1 Create integration test for DRS API
    - Test against real DRS service in TEST account
    - Verify describe_source_servers returns real servers
    - Check server IDs match expected format
    - Validate replication status is CONTINUOUS
    - _Requirements: 10.5_

  - [ ] 12.2 Create integration test for DynamoDB persistence
    - Write execution history to real DynamoDB table
    - Query records and verify data integrity
    - Test concurrent writes
    - Measure query performance (<200ms)
    - _Requirements: 5.1, 5.2, 5.3, 7.5_

  - [ ] 12.3 Create integration test for Step Functions
    - Start real Step Functions execution
    - Monitor state transitions
    - Verify state machine completes successfully
    - Check CloudWatch Logs for execution trace
    - _Requirements: 1.1, 1.2, 4.3_

  - [ ]* 12.4 Create integration test for cross-account IAM
    - Assume cross-account role (if available)
    - Verify temporary credentials work
    - Test credential refresh
    - _Requirements: 6.1, 6.2, 6.4_

- [ ] 13. Implement end-to-end tests
  - [ ]* 13.1 Create E2E test for basic recovery
    - Execute 1-wave recovery plan in drill mode
    - Use 2 real DRS servers
    - Verify instances launched and healthy
    - Terminate drill instances after test
    - _Requirements: 10.2, 10.3_

  - [ ]* 13.2 Create E2E test for multi-wave recovery
    - Execute 3-wave recovery plan
    - Use 6 real DRS servers (2 per wave)
    - Verify wave dependencies enforced
    - Measure total execution time (<15 minutes)
    - _Requirements: 1.1, 1.2, 7.1_

  - [ ]* 13.3 Create E2E test for parallel execution
    - Execute wave with 4 servers in parallel
    - Verify all servers launch simultaneously
    - Check all instances reach running state
    - _Requirements: 1.4, 7.2_

  - [ ]* 13.4 Create E2E test for error recovery
    - Simulate server failure (invalid server ID)
    - Verify error handling and cascading failure
    - Check execution history records error details
    - _Requirements: 4.1, 4.2, 5.4_

- [ ] 14. Implement performance tests
  - [ ]* 14.1 Create performance test for small load
    - 6 servers, 3 waves
    - Target: <5 minutes total execution time
    - Measure wave initiation time (<5 seconds)
    - _Requirements: 7.1_

  - [ ]* 14.2 Create performance test for medium load
    - 20 servers, 5 waves
    - Target: <15 minutes total execution time
    - Verify no DRS API throttling
    - _Requirements: 7.2_

  - [ ]* 14.3 Create performance test for DynamoDB queries
    - Seed 1000 execution history records
    - Measure query performance
    - Target: <200ms response time
    - _Requirements: 7.5_

- [ ] 15. Set up continuous integration
  - Create GitHub Actions workflow (or AWS CodePipeline)
  - Configure unit test job (runs on every commit)
  - Configure integration test job (runs on PR)
  - Configure E2E test job (runs on main branch only)
  - Set up code coverage reporting (Codecov)
  - Define quality gates (80% coverage, all tests pass)

- [ ] 16. Final checkpoint - Ensure all tests pass
  - Run complete test suite: `pytest tests/ -v`
  - Verify unit test coverage > 80%
  - Verify all integration tests pass
  - Verify E2E tests pass (if run)
  - Generate test report
  - Ask user if questions arise
