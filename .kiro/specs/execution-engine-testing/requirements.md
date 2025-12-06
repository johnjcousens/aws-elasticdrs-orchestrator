# Requirements Document
# Execution Engine Testing

## Introduction

The Execution Engine is the core orchestration component of the AWS DRS Orchestration system, responsible for coordinating wave-based disaster recovery operations through AWS Step Functions. Despite being 100% implemented (556 lines of Python code), it currently has **0% test coverage**, representing the highest-risk gap in the system.

This specification defines comprehensive testing requirements to validate the Execution Engine's correctness, reliability, and performance before production deployment.

## Glossary

- **Execution Engine**: AWS Step Functions state machine + orchestration Lambda that coordinates wave-based recovery
- **Wave**: A group of servers recovered together in a specific order with dependencies
- **DRS**: AWS Elastic Disaster Recovery Service - provides server replication and recovery APIs
- **Drill Mode**: Non-disruptive test recovery that doesn't affect production systems
- **Health Check**: Post-recovery validation that EC2 instances are running and accessible
- **Step Functions**: AWS service that orchestrates Lambda functions as a state machine
- **Source Server**: A server being replicated by DRS (identified by s-{17 hex chars})
- **Recovery Job**: DRS API operation that launches a recovered EC2 instance

## Requirements

### Requirement 1: Wave Orchestration Testing

**User Story:** As a QA engineer, I want to validate wave-based orchestration logic, so that I can ensure waves execute in the correct order with proper dependency handling.

#### Acceptance Criteria

1. WHEN a recovery plan with 3 sequential waves is executed THEN the Execution Engine SHALL execute Wave 1, then Wave 2, then Wave 3 in order
2. WHEN Wave 2 depends on Wave 1 THEN the Execution Engine SHALL wait for Wave 1 to complete before starting Wave 2
3. WHEN a wave has WaitTimeSeconds configured THEN the Execution Engine SHALL pause for the specified duration before starting the next wave
4. WHEN a wave is configured for PARALLEL execution THEN the Execution Engine SHALL launch all servers in that wave simultaneously
5. WHEN a wave is configured for SEQUENTIAL execution THEN the Execution Engine SHALL launch servers one at a time in ExecutionOrder

---

### Requirement 2: DRS API Integration Testing

**User Story:** As a QA engineer, I want to validate DRS API integration, so that I can ensure the system correctly calls AWS DRS to perform recovery operations.

#### Acceptance Criteria

1. WHEN the Execution Engine starts a recovery job THEN it SHALL call drs.start_recovery with correct sourceServerID and recoverySnapshotID parameters
2. WHEN isDrill is True THEN the Execution Engine SHALL pass isDrill=True to the DRS API for non-disruptive testing
3. WHEN the Execution Engine monitors job status THEN it SHALL call drs.describe_jobs and correctly parse job status (PENDING, IN_PROGRESS, COMPLETED, FAILED)
4. WHEN a DRS API call fails with throttling THEN the Execution Engine SHALL retry with exponential backoff up to 3 attempts
5. WHEN a source server does not exist THEN the Execution Engine SHALL return a clear error message identifying the missing server

---

### Requirement 3: Health Check Validation Testing

**User Story:** As a QA engineer, I want to validate post-recovery health checks, so that I can ensure recovered instances are verified as healthy before proceeding.

#### Acceptance Criteria

1. WHEN a recovery job completes THEN the Execution Engine SHALL call ec2.describe_instance_status for the recovered instance
2. WHEN an instance status is "running" THEN the Execution Engine SHALL mark the server as successfully recovered
3. WHEN an instance status is "pending" THEN the Execution Engine SHALL wait up to 5 minutes polling every 30 seconds
4. WHEN an instance fails to reach "running" state within 5 minutes THEN the Execution Engine SHALL mark the recovery as FAILED
5. WHEN health checks are disabled for a wave THEN the Execution Engine SHALL skip health validation and proceed immediately

---

### Requirement 4: Error Handling and Recovery Testing

**User Story:** As a QA engineer, I want to validate error handling behavior, so that I can ensure the system fails gracefully and provides actionable error messages.

#### Acceptance Criteria

1. WHEN a DRS recovery job fails THEN the Execution Engine SHALL capture the error message and store it in execution history
2. WHEN a wave fails THEN the Execution Engine SHALL mark subsequent dependent waves as SKIPPED
3. WHEN a Step Functions execution times out THEN the Execution Engine SHALL mark the execution as FAILED with timeout reason
4. WHEN network connectivity to DRS API is lost THEN the Execution Engine SHALL retry with exponential backoff before failing
5. WHEN an execution is cancelled by a user THEN the Execution Engine SHALL gracefully stop and mark status as CANCELLED

---

### Requirement 5: Execution History Persistence Testing

**User Story:** As a QA engineer, I want to validate execution history tracking, so that I can ensure complete audit trails are maintained for compliance.

#### Acceptance Criteria

1. WHEN an execution starts THEN the Execution Engine SHALL create a record in DynamoDB with ExecutionId, PlanId, Status=RUNNING, and StartTime
2. WHEN a wave completes THEN the Execution Engine SHALL update the execution record with wave status, server results, and timing
3. WHEN an execution completes THEN the Execution Engine SHALL update EndTime and final Status (COMPLETED or FAILED)
4. WHEN a server recovery fails THEN the Execution Engine SHALL record the server ID, error message, and DRS job ID in execution history
5. WHEN execution history is queried THEN all fields SHALL be present and correctly formatted (no null values for required fields)

---

### Requirement 6: Cross-Account Recovery Testing

**User Story:** As a QA engineer, I want to validate cross-account recovery operations, so that I can ensure the system works in multi-account enterprise scenarios.

#### Acceptance Criteria

1. WHEN a recovery plan specifies a target account THEN the Execution Engine SHALL assume the cross-account IAM role using STS
2. WHEN role assumption succeeds THEN the Execution Engine SHALL use temporary credentials for all DRS API calls
3. WHEN role assumption fails THEN the Execution Engine SHALL return a clear error message with the role ARN and reason
4. WHEN temporary credentials expire during execution THEN the Execution Engine SHALL refresh credentials automatically
5. WHEN cross-account recovery completes THEN execution history SHALL record both source and target account IDs

---

### Requirement 7: Performance and Scalability Testing

**User Story:** As a QA engineer, I want to validate performance under load, so that I can ensure the system meets RTO requirements for production use.

#### Acceptance Criteria

1. WHEN recovering 6 servers in parallel THEN the Execution Engine SHALL complete within 15 minutes (RTO target)
2. WHEN recovering 20 servers across 5 waves THEN the Execution Engine SHALL handle all DRS API calls without throttling errors
3. WHEN monitoring 10 concurrent recovery jobs THEN the Execution Engine SHALL poll status efficiently without exceeding Lambda timeout
4. WHEN Step Functions processes 100 state transitions THEN execution SHALL complete without hitting service limits
5. WHEN execution history contains 1000 records THEN DynamoDB queries SHALL return results within 200ms

---

### Requirement 8: SNS Notification Testing

**User Story:** As a QA engineer, I want to validate notification delivery, so that I can ensure stakeholders are informed of execution status.

#### Acceptance Criteria

1. WHEN an execution completes successfully THEN the Execution Engine SHALL publish an SNS message with execution summary
2. WHEN an execution fails THEN the Execution Engine SHALL publish an SNS message with error details and affected servers
3. WHEN SNS topic ARN is not configured THEN the Execution Engine SHALL skip notification without failing the execution
4. WHEN SNS publish fails THEN the Execution Engine SHALL log the error but continue execution
5. WHEN notification is sent THEN it SHALL include ExecutionId, PlanId, Status, Duration, and Server Count

---

### Requirement 9: Idempotency and Retry Testing

**User Story:** As a QA engineer, I want to validate retry behavior, so that I can ensure transient failures don't cause data corruption.

#### Acceptance Criteria

1. WHEN a Lambda invocation fails THEN Step Functions SHALL retry up to 3 times with exponential backoff
2. WHEN the same execution is started twice THEN the Execution Engine SHALL detect duplicate and return existing ExecutionId
3. WHEN a DRS API call is retried THEN it SHALL not create duplicate recovery jobs
4. WHEN execution history update fails THEN the Execution Engine SHALL retry the DynamoDB write operation
5. WHEN all retries are exhausted THEN the Execution Engine SHALL fail with a clear error message

---

### Requirement 10: Integration with Real DRS Environment

**User Story:** As a QA engineer, I want to test against real DRS servers, so that I can validate end-to-end functionality in a production-like environment.

#### Acceptance Criteria

1. WHEN testing with real DRS servers THEN the test environment SHALL have 6 Windows servers in CONTINUOUS replication state
2. WHEN executing a drill recovery THEN real EC2 instances SHALL be launched and validated
3. WHEN drill completes THEN test instances SHALL be automatically terminated to avoid costs
4. WHEN testing in us-east-1 region THEN all 6 test servers SHALL be available (s-3d75cdc0d9a28a725, s-3afa164776f93ce4f, etc.)
5. WHEN real DRS API calls are made THEN responses SHALL match expected schema and timing

---

### Requirement 11: Mocking and Unit Test Infrastructure

**User Story:** As a developer, I want comprehensive mocking infrastructure, so that I can write fast, reliable unit tests without AWS dependencies.

#### Acceptance Criteria

1. WHEN unit testing wave orchestration THEN DRS API calls SHALL be mocked with realistic responses
2. WHEN mocking DRS responses THEN job status transitions SHALL follow realistic timing (PENDING → IN_PROGRESS → COMPLETED)
3. WHEN testing error scenarios THEN mocks SHALL simulate throttling, timeouts, and API errors
4. WHEN running unit tests THEN no real AWS API calls SHALL be made (verified by network monitoring)
5. WHEN mocks are configured THEN they SHALL support both success and failure scenarios for all DRS operations

---

### Requirement 12: Test Data Management

**User Story:** As a QA engineer, I want well-defined test data, so that I can create reproducible test scenarios.

#### Acceptance Criteria

1. WHEN creating test recovery plans THEN test data SHALL include 3 Protection Groups (Database, Application, Web) with 2 servers each
2. WHEN defining test waves THEN scenarios SHALL cover: single wave, multi-wave with dependencies, parallel execution, sequential execution
3. WHEN testing error scenarios THEN test data SHALL include: invalid server IDs, missing Protection Groups, circular dependencies
4. WHEN test data is used THEN it SHALL match the schema in DynamoDB (PascalCase field names)
5. WHEN tests complete THEN test data SHALL be cleaned up automatically (no orphaned records)
