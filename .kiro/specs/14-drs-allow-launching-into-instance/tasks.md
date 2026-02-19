# DRS AllowLaunchingIntoThisInstance - Implementation Tasks

## Overview

Implementation tasks for the DRS AllowLaunchingIntoThisInstance pattern, organized into 9 phases over 9 weeks.

**Integration Strategy**: Integrate into existing Lambda handlers (data-management, execution, query) based on operation type, NOT as a new handler.

**Key Components**:
- 4 new shared modules (instance_matcher, drs_client, drs_job_monitor, drs_error_handler)
- 3 DynamoDB tables (config, executions, failback state)
- 15+ API Gateway endpoints across 3 handlers
- Dual invocation pattern support (API Gateway + Direct Lambda)
- EventBridge integration for execution monitoring
- Step Functions integration for wave-based orchestration

**Total Tasks**: 234 tasks
- Phase 1 (Foundation): 20 tasks (DynamoDB, data models, exceptions)
- Phase 2 (Instance Matching): 17 tasks (matching algorithm, cross-account, validation)
- Phase 3 (DRS Client): 15 tasks (DRS API wrapper, launch configuration, error handling)
- Phase 4 (Job Monitoring): 15 tasks (monitoring, status tracking, timeout handling)
- Phase 5 (Data Management Handler): 20 tasks (configuration operations, CloudFormation resources)
- Phase 6 (Execution Handler): 44 tasks (failover/failback workflows, agent integration, EventBridge)
- Phase 7 (Query Handler): 38 tasks (query operations, IP preservation, DynamoDB schema)
- Phase 8 (Testing & Documentation): 37 tasks (E2E tests, integration tests, docs, performance, monitoring)
- Phase 9 (Production Rollout): 28 tasks (deployment, validation, monitoring, rollback)

**Test Coverage**: 104 tests (59 unit + 37 integration + 8 E2E)

## Phase 1: Foundation & Data Models (Week 1)

### 1.1 DynamoDB Tables

- [ ] 1.1.1 Create DRSAllowLaunchingConfigTable CloudFormation resource
- [ ] 1.1.2 Create DRSRecoveryExecutionsTable CloudFormation resource (extend existing)
- [ ] 1.1.3 Create DRSFailbackStateTable CloudFormation resource
- [ ] 1.1.4 Add GSI indexes (AccountIndex, StatusIndex, ExecutionTypeIndex, WaveIndex)
- [ ] 1.1.5 Configure TTL for automatic cleanup (90 days)
- [ ] 1.1.6 Test table creation and index queries

### 1.2 Data Models

- [ ] 1.2.1 Create `InstanceMatchingConfig` data model class
- [ ] 1.2.2 Create `RecoveryExecution` data model class (extend existing)
- [ ] 1.2.3 Create `FailbackState` data model class
- [ ] 1.2.4 Add validation methods to data models
- [ ] 1.2.5 Add serialization/deserialization methods
- [ ] 1.2.6 Write unit tests for data models (6 tests)

### 1.3 Custom Exceptions

- [ ] 1.3.1 Create `InstanceMatchingError` exception class
- [ ] 1.3.2 Create `ConfigurationError` exception class
- [ ] 1.3.3 Create `ValidationError` exception class
- [ ] 1.3.4 Create `RecoveryError` exception class
- [ ] 1.3.5 Create `AgentInstallationError` exception class
- [ ] 1.3.6 Create `PrivateIPMismatchError` exception class
- [ ] 1.3.7 Add `to_dict()` methods for API responses
- [ ] 1.3.8 Write unit tests for exception handling (8 tests)

## Phase 2: Instance Matching Component (Week 2)

### 2.1 InstanceMatcher Core (`lambda/shared/instance_matcher.py`)

- [ ] 2.1.1 Create `InstanceMatcher` class skeleton
- [ ] 2.1.2 Implement `match_instances()` method
- [ ] 2.1.3 Implement `_get_source_instances()` method
- [ ] 2.1.4 Implement `_get_target_instances()` method
- [ ] 2.1.5 Implement `_match_by_name_tag()` method
- [ ] 2.1.6 Implement `_validate_match()` method
- [ ] 2.1.7 Write unit tests for instance matching (12 tests)

### 2.2 Cross-Account Support

- [ ] 2.2.1 Implement cross-account IAM role assumption
- [ ] 2.2.2 Add external ID validation
- [ ] 2.2.3 Implement credential caching
- [ ] 2.2.4 Add error handling for AssumeRole failures
- [ ] 2.2.5 Write unit tests for cross-account operations (6 tests)

### 2.3 Matching Validation

- [ ] 2.3.1 Implement instance type compatibility check
- [ ] 2.3.2 Implement subnet compatibility check
- [ ] 2.3.3 Implement security group validation
- [ ] 2.3.4 Implement tag validation
- [ ] 2.3.5 Write unit tests for validation logic (8 tests)

## Phase 3: DRS Client Component (Week 3)

### 3.1 DRSClient Core (`lambda/shared/drs_client.py`)

- [ ] 3.1.1 Create `DRSClient` class skeleton
- [ ] 3.1.2 Implement `configure_allow_launching_into_instance()` method
- [ ] 3.1.3 Implement `start_recovery()` method with staging account tracking
- [ ] 3.1.4 Implement `get_recovery_status()` method
- [ ] 3.1.5 Implement `reverse_replication()` method
- [ ] 3.1.6 Write unit tests for DRS operations (10 tests)

### 3.2 Launch Configuration

- [ ] 3.2.1 Implement `_update_launch_configuration()` method
- [ ] 3.2.2 Add `launchIntoEC2InstanceID` parameter handling
- [ ] 3.2.3 Add `copyPrivateIp` parameter handling
- [ ] 3.2.4 Add `copyTags` parameter handling
- [ ] 3.2.5 Write unit tests for launch configuration (6 tests)

### 3.3 Error Handling

- [ ] 3.3.1 Implement retry logic for transient DRS API errors
- [ ] 3.3.2 Add exponential backoff for rate limiting
- [ ] 3.3.3 Implement error classification (retryable vs non-retryable)
- [ ] 3.3.4 Write unit tests for error handling (5 tests)

## Phase 4: Recovery Job Monitoring (Week 4)

### 4.1 RecoveryJobMonitor Core (`lambda/shared/drs_job_monitor.py`)

- [ ] 4.1.1 Create `RecoveryJobMonitor` class skeleton
- [ ] 4.1.2 Implement `monitor_until_completion()` method
- [ ] 4.1.3 Implement `_poll_job_status()` method
- [ ] 4.1.4 Implement `_check_server_launch_status()` method
- [ ] 4.1.5 Implement `_get_recovery_instances()` method
- [ ] 4.1.6 Write unit tests for monitoring (8 tests)

### 4.2 Status Tracking

- [ ] 4.2.1 Implement DynamoDB status updates
- [ ] 4.2.2 Add CloudWatch metrics publishing
- [ ] 4.2.3 Implement progress percentage calculation
- [ ] 4.2.4 Add estimated completion time calculation
- [ ] 4.2.5 Write unit tests for status tracking (6 tests)

### 4.3 Timeout & Cancellation

- [ ] 4.3.1 Implement timeout handling
- [ ] 4.3.2 Implement graceful cancellation
- [ ] 4.3.3 Add cleanup on timeout/cancellation
- [ ] 4.3.4 Write unit tests for timeout scenarios (4 tests)

## Phase 5: Data Management Handler Integration (Week 5)

### 5.1 Configuration Operations (`lambda/data-management-handler/index.py`)

- [ ] 5.1.1 Add route handler for `POST /protection-groups/{id}/instance-pairs` in `handle_api_gateway_request()`
- [ ] 5.1.2 Add route handler for `PUT /protection-groups/{id}/instance-pairs/{pairId}` in `handle_api_gateway_request()`
- [ ] 5.1.3 Add route handler for `DELETE /protection-groups/{id}/instance-pairs/{pairId}` in `handle_api_gateway_request()`
- [ ] 5.1.4 Add route handler for `POST /protection-groups/{id}/configure-allow-launching` in `handle_api_gateway_request()`
- [ ] 5.1.5 Implement `handle_configure_instance_pairs()` function with instance matcher integration
- [ ] 5.1.6 Implement `handle_update_instance_pair()` function with DynamoDB updates
- [ ] 5.1.7 Implement `handle_delete_instance_pair()` function with DynamoDB cleanup
- [ ] 5.1.8 Implement `handle_configure_allow_launching()` function with DRS client integration
- [ ] 5.1.9 Add direct invocation operation handlers in `handle_direct_invocation()`
- [ ] 5.1.10 Add dual invocation pattern support (API Gateway + Direct Lambda)
- [ ] 5.1.11 Write unit tests for configuration operations (12 tests)

### 5.2 CloudFormation Resources

- [ ] 5.2.1 Add `ProtectionGroupInstancePairsResource` to `api-gateway-resources-stack.yaml`
- [ ] 5.2.2 Add `ProtectionGroupInstancePairByIdResource` to `api-gateway-resources-stack.yaml`
- [ ] 5.2.3 Add `ProtectionGroupConfigureAllowLaunchingResource` to `api-gateway-resources-stack.yaml`
- [ ] 5.2.4 Add `ProtectionGroupInstancePairsPostMethod` to `api-gateway-core-methods-stack.yaml`
- [ ] 5.2.5 Add `ProtectionGroupInstancePairPutMethod` to `api-gateway-core-methods-stack.yaml`
- [ ] 5.2.6 Add `ProtectionGroupInstancePairDeleteMethod` to `api-gateway-core-methods-stack.yaml`
- [ ] 5.2.7 Add `ProtectionGroupConfigureAllowLaunchingPostMethod` to `api-gateway-core-methods-stack.yaml`
- [ ] 5.2.8 Configure Lambda integration with data-management-handler
- [ ] 5.2.9 Write integration tests for configuration API endpoints (4 tests)

## Phase 6: Execution Handler Integration (Week 6)

### 6.1 Execution Operations (`lambda/execution-handler/index.py`)

- [ ] 6.1.1 Add route handler for `POST /executions/allow-launching/failover` in `handle_api_gateway_request()`
- [ ] 6.1.2 Add route handler for `POST /executions/allow-launching/failback` in `handle_api_gateway_request()`
- [ ] 6.1.3 Add route handler for `GET /executions/{id}/allow-launching/status` in `handle_api_gateway_request()`
- [ ] 6.1.4 Implement `handle_allow_launching_failover()` function with full workflow (discovery, validation, configuration, recovery, validation)
- [ ] 6.1.5 Implement `handle_allow_launching_failback()` function with reverse replication workflow
- [ ] 6.1.6 Implement `handle_allow_launching_status()` function with detailed status tracking
- [ ] 6.1.7 Add direct invocation operation handlers in `handle_direct_invocation()`
- [ ] 6.1.8 Add dual invocation pattern support (API Gateway + Direct Lambda)
- [ ] 6.1.9 Integrate with existing Step Functions state machine for wave-based orchestration
- [ ] 6.1.10 Write unit tests for execution operations (12 tests)

### 6.2 CloudFormation Resources

- [ ] 6.2.1 Add `ExecutionsAllowLaunchingResource` to `api-gateway-resources-stack.yaml`
- [ ] 6.2.2 Add `ExecutionsAllowLaunchingFailoverResource` to `api-gateway-resources-stack.yaml`
- [ ] 6.2.3 Add `ExecutionsAllowLaunchingFailbackResource` to `api-gateway-resources-stack.yaml`
- [ ] 6.2.4 Add `ExecutionAllowLaunchingStatusResource` to `api-gateway-resources-stack.yaml`
- [ ] 6.2.5 Add `ExecutionAllowLaunchingStatusDetailResource` to `api-gateway-resources-stack.yaml`
- [ ] 6.2.6 Add `ExecutionsAllowLaunchingFailoverPostMethod` to `api-gateway-operations-methods-stack.yaml`
- [ ] 6.2.7 Add `ExecutionsAllowLaunchingFailbackPostMethod` to `api-gateway-operations-methods-stack.yaml`
- [ ] 6.2.8 Add `ExecutionAllowLaunchingStatusGetMethod` to `api-gateway-operations-methods-stack.yaml`
- [ ] 6.2.9 Configure Lambda integration with execution-handler
- [ ] 6.2.10 Write integration tests for execution API endpoints (4 tests)

### 6.3 DRS Agent Deployer Integration

- [ ] 6.3.1 Implement `_install_agent_on_recovery_instance()` method in execution handler
- [ ] 6.3.2 Add Lambda invocation for DRS Agent Deployer with proper event structure
- [ ] 6.3.3 Implement agent installation status polling with timeout handling
- [ ] 6.3.4 Add error handling for agent installation failures with remediation guidance
- [ ] 6.3.5 Integrate agent installation into failback workflow
- [ ] 6.3.6 Write unit tests for agent installation (6 tests)

### 6.4 Reverse Replication

- [ ] 6.4.1 Implement `initiate_reverse_replication()` method using DRS client
- [ ] 6.4.2 Add prerequisite validation before reverse replication (network, security groups, IAM)
- [ ] 6.4.3 Implement `_get_original_staging_account()` helper method from DynamoDB
- [ ] 6.4.4 Implement `_save_failback_state()` helper method to DynamoDB
- [ ] 6.4.5 Implement reverse replication monitoring with lag tracking
- [ ] 6.4.6 Add CONTINUOUS state detection with configurable lag threshold
- [ ] 6.4.7 Write unit tests for reverse replication (8 tests)

### 6.5 Staging Account Tracking

- [ ] 6.5.1 Update `start_recovery()` to track staging account ID in DynamoDB
- [ ] 6.5.2 Add staging account validation for non-drill recoveries
- [ ] 6.5.3 Implement staging account retrieval from DynamoDB for failback
- [ ] 6.5.4 Add staging account consistency checks across recovery instances
- [ ] 6.5.5 Implement staging account error handling and remediation
- [ ] 6.5.6 Write unit tests for staging account tracking (6 tests)

### 6.6 EventBridge Integration

- [ ] 6.6.1 Extend existing EventBridge polling rule for AllowLaunchingIntoThisInstance executions
- [ ] 6.6.2 Add instance identity preservation validation to polling logic
- [ ] 6.6.3 Add private IP preservation validation to polling logic
- [ ] 6.6.4 Add reverse replication progress tracking to polling logic
- [ ] 6.6.5 Write unit tests for EventBridge integration (4 tests)

## Phase 7: Query Handler Integration (Week 7)

### 7.1 Query Operations (`lambda/query-handler/index.py`)

- [ ] 7.1.1 Add route handler for `POST /drs/instances/match` in `handle_api_gateway_request()`
- [ ] 7.1.2 Add route handler for `POST /drs/instances/validate-pairs` in `handle_api_gateway_request()`
- [ ] 7.1.3 Add route handler for `POST /drs/instances/validate-ip` in `handle_api_gateway_request()`
- [ ] 7.1.4 Implement `handle_match_instances()` function with instance matcher integration
- [ ] 7.1.5 Implement `handle_validate_instance_pairs()` function with comprehensive validation
- [ ] 7.1.6 Implement `handle_validate_ip_preservation()` function with IP tracking
- [ ] 7.1.7 Add direct invocation operation handlers in `handle_direct_invocation()`
- [ ] 7.1.8 Add dual invocation pattern support (API Gateway + Direct Lambda)
- [ ] 7.1.9 Write unit tests for query operations (12 tests)

### 7.2 CloudFormation Resources

- [ ] 7.2.1 Add `DrsInstancesResource` to `api-gateway-resources-stack.yaml`
- [ ] 7.2.2 Add `DrsInstancesMatchResource` to `api-gateway-resources-stack.yaml`
- [ ] 7.2.3 Add `DrsInstancesValidatePairsResource` to `api-gateway-resources-stack.yaml`
- [ ] 7.2.4 Add `DrsInstancesValidateIpResource` to `api-gateway-resources-stack.yaml`
- [ ] 7.2.5 Add `DrsInstancesMatchPostMethod` to `api-gateway-infrastructure-methods-stack.yaml`
- [ ] 7.2.6 Add `DrsInstancesValidatePairsPostMethod` to `api-gateway-infrastructure-methods-stack.yaml`
- [ ] 7.2.7 Add `DrsInstancesValidateIpPostMethod` to `api-gateway-infrastructure-methods-stack.yaml`
- [ ] 7.2.8 Configure Lambda integration with query-handler
- [ ] 7.2.9 Write integration tests for query API endpoints (4 tests)

### 7.3 Private IP Preservation

- [ ] 7.3.1 Implement `_capture_source_private_ip()` method in query handler
- [ ] 7.3.2 Implement `_capture_target_private_ip()` method in query handler
- [ ] 7.3.3 Implement `validate_recovery_instances()` method with IP validation
- [ ] 7.3.4 Add `_get_expected_instance_for_source()` helper method
- [ ] 7.3.5 Implement IP comparison logic with detailed error messages
- [ ] 7.3.6 Write unit tests for IP capture and validation (8 tests)

### 7.4 IP Mismatch Handling

- [ ] 7.4.1 Implement `PrivateIPMismatchError` exception with detailed context
- [ ] 7.4.2 Add IP mismatch detection logic in validation workflow
- [ ] 7.4.3 Implement remediation guidance generation for IP mismatches
- [ ] 7.4.4 Add IP validation before failback with blocking errors
- [ ] 7.4.5 Implement IP mismatch logging and CloudWatch metrics
- [ ] 7.4.6 Write unit tests for IP mismatch scenarios (6 tests)

### 7.5 DynamoDB Schema Updates

- [ ] 7.5.1 Add `source_private_ip` field to recovery_instances array in DRSRecoveryExecutionsTable
- [ ] 7.5.2 Add `target_private_ip` field to recovery_instances array in DRSRecoveryExecutionsTable
- [ ] 7.5.3 Add `recovery_private_ip` field to recovery_instances array in DRSRecoveryExecutionsTable
- [ ] 7.5.4 Add `recovery_instance_private_ip` field to DRSFailbackStateTable
- [ ] 7.5.5 Add `private_ip_validated` field to DRSFailbackStateTable
- [ ] 7.5.6 Add `original_instance_private_ip` field to DRSFailbackStateTable
- [ ] 7.5.7 Update CloudFormation templates with new schema fields
- [ ] 7.5.8 Write unit tests for schema updates (4 tests)

## Phase 8: Testing & Documentation (Week 8)

### 8.1 End-to-End Tests

- [ ] 8.1.1 Write E2E test for complete failover workflow (discovery → matching → configuration → recovery → validation)
- [ ] 8.1.2 Write E2E test for complete failback workflow (reverse replication → agent installation → failback → validation)
- [ ] 8.1.3 Write E2E test for failover with IP preservation validation
- [ ] 8.1.4 Write E2E test for failback with IP validation and mismatch detection
- [ ] 8.1.5 Write E2E test for multi-wave recovery with AllowLaunchingIntoThisInstance
- [ ] 8.1.6 Write E2E test for drill mode with instance identity preservation
- [ ] 8.1.7 Write E2E test for error scenarios (validation failures, recovery failures, agent failures)
- [ ] 8.1.8 Write E2E test for cross-account operations with external ID validation

### 8.2 Integration Tests

- [ ] 8.2.1 Write integration test for instance matching across accounts with fuzzy matching
- [ ] 8.2.2 Write integration test for DRS configuration with conflicting settings
- [ ] 8.2.3 Write integration test for recovery job monitoring with timeout handling
- [ ] 8.2.4 Write integration test for agent installation with network validation
- [ ] 8.2.5 Write integration test for reverse replication with lag monitoring
- [ ] 8.2.6 Write integration test for staging account tracking across failover/failback
- [ ] 8.2.7 Write integration test for private IP preservation across full cycle
- [ ] 8.2.8 Write integration test for API Gateway endpoints with authentication
- [ ] 8.2.9 Write integration test for handler integration (data-management, execution, query)
- [ ] 8.2.10 Write integration test for error handling and retry logic with exponential backoff

### 8.3 Documentation

- [ ] 8.3.1 Create `FAILOVER_FAILBACK_WORKFLOWS.md` reference doc with sequence diagrams
- [ ] 8.3.2 Create `INSTANCE_MATCHING_ALGORITHM.md` reference doc with matching logic details
- [ ] 8.3.3 Create `DRS_LAUNCH_CONFIGURATION.md` reference doc with configuration parameters
- [ ] 8.3.4 Create `TESTING_STRATEGY.md` reference doc with test coverage details
- [ ] 8.3.5 Update main README with AllowLaunchingIntoThisInstance section and usage examples
- [ ] 8.3.6 Create API documentation for new endpoints with request/response examples
- [ ] 8.3.7 Create troubleshooting guide with common errors and remediation steps
- [ ] 8.3.8 Create deployment guide with phase-by-phase rollout instructions

### 8.4 Performance Testing

- [ ] 8.4.1 Test failover performance with 10, 50, 100 instances (target: <5, <15, <30 minutes)
- [ ] 8.4.2 Test failback performance with reverse replication duration tracking
- [ ] 8.4.3 Test instance matching performance with 100+ instances (target: <10 seconds)
- [ ] 8.4.4 Test concurrent recovery operations with multiple jobs
- [ ] 8.4.5 Optimize slow operations (instance discovery, configuration updates, monitoring)
- [ ] 8.4.6 Document performance benchmarks with P50, P95, P99 latencies

### 8.5 CloudWatch Monitoring

- [ ] 8.5.1 Create CloudWatch dashboard for AllowLaunchingIntoThisInstance metrics
- [ ] 8.5.2 Configure CloudWatch alarms for critical failures (recovery, agent, replication)
- [ ] 8.5.3 Create CloudWatch Logs Insights queries for troubleshooting
- [ ] 8.5.4 Document monitoring and alerting strategy
- [ ] 8.5.5 Test alarm notifications and escalation procedures

## Phase 9: Production Rollout (Week 9)

### 9.1 Deployment

- [ ] 9.1.1 Deploy DynamoDB tables to dev environment (DRSAllowLaunchingConfigTable, DRSRecoveryExecutionsTable, DRSFailbackStateTable)
- [ ] 9.1.2 Deploy shared modules to Lambda layer (instance_matcher, drs_client, drs_job_monitor, drs_error_handler)
- [ ] 9.1.3 Deploy updated data-management-handler to dev with new routes and operations
- [ ] 9.1.4 Deploy updated execution-handler to dev with failover/failback workflows
- [ ] 9.1.5 Deploy updated query-handler to dev with matching and validation operations
- [ ] 9.1.6 Deploy CloudFormation API Gateway updates to dev (resources and methods)
- [ ] 9.1.7 Run smoke tests in dev environment (all endpoints, basic workflows)
- [ ] 9.1.8 Deploy to test environment with full validation
- [ ] 9.1.9 Execute DR drill in test environment with AllowLaunchingIntoThisInstance
- [ ] 9.1.10 Deploy to production environment with phased rollout

### 9.2 Validation

- [ ] 9.2.1 Validate all API endpoints functional (configuration, execution, query)
- [ ] 9.2.2 Validate instance matching accuracy (>99% match rate)
- [ ] 9.2.3 Validate failover RTO < 30 minutes for 100 instances
- [ ] 9.2.4 Validate failback RTO < 30 minutes with reverse replication
- [ ] 9.2.5 Validate private IP preservation (100% preservation rate)
- [ ] 9.2.6 Validate staging account tracking across failover/failback cycle
- [ ] 9.2.7 Validate agent installation success rate (>95%)
- [ ] 9.2.8 Validate error handling and recovery for all failure scenarios

### 9.3 Monitoring

- [ ] 9.3.1 Configure CloudWatch alarms for critical metrics (recovery failures, agent failures, IP mismatches)
- [ ] 9.3.2 Create CloudWatch dashboard with key metrics (RTO, match rate, success rate)
- [ ] 9.3.3 Set up log insights queries for troubleshooting (failed recoveries, IP mismatches, agent errors)
- [ ] 9.3.4 Configure SNS notifications for alarm escalation
- [ ] 9.3.5 Monitor for 48 hours post-deployment with on-call support

### 9.4 Rollback Plan

- [ ] 9.4.1 Document rollback procedures for each deployment phase
- [ ] 9.4.2 Test rollback in dev environment
- [ ] 9.4.3 Prepare rollback scripts for quick execution
- [ ] 9.4.4 Define rollback triggers and decision criteria
- [ ] 9.4.5 Communicate rollback plan to stakeholders

## Test Coverage Summary

### Unit Tests (59 tests)
- Data Models: 6 tests
- Exception Handling: 8 tests
- Instance Matching: 12 tests
- Cross-Account Operations: 6 tests
- Validation Logic: 8 tests
- DRS Operations: 10 tests
- Launch Configuration: 6 tests
- Error Handling: 5 tests
- Monitoring: 8 tests
- Status Tracking: 6 tests
- Timeout Scenarios: 4 tests
- Configuration Operations (data-management-handler): 12 tests
- Execution Operations (execution-handler): 12 tests
- Query Operations (query-handler): 12 tests
- Agent Installation: 6 tests
- Reverse Replication: 8 tests
- Staging Account Tracking: 6 tests
- IP Capture & Validation: 8 tests
- IP Mismatch Scenarios: 6 tests
- Schema Updates: 4 tests

### Integration Tests (37 tests)
- Configuration API Endpoints: 4 tests
- Execution API Endpoints: 4 tests
- Query API Endpoints: 4 tests
- Instance Matching: 1 test
- DRS Configuration: 1 test
- Recovery Monitoring: 1 test
- Agent Installation: 1 test
- Reverse Replication: 1 test
- Staging Account Tracking: 1 test
- Private IP Preservation: 1 test
- API Gateway: 1 test
- Handler Integration: 1 test
- Error Handling: 1 test

### End-to-End Tests (8 tests)
- Complete Failover: 1 test
- Complete Failback: 1 test
- Failover with IP Preservation: 1 test
- Failback with IP Validation: 1 test
- Multi-Wave Recovery: 1 test
- Drill Mode: 1 test
- Error Scenarios: 1 test
- Cross-Account Operations: 1 test

**Total Tests**: 104 tests (59 unit + 37 integration + 8 E2E)

## Dependencies

### External Dependencies
- AWS SDK (boto3)
- DRS Agent Deployer Lambda function (existing)
- DynamoDB tables
- IAM roles and policies

### Internal Dependencies
- `shared/cross_account.py` - Cross-account IAM operations
- `shared/drs_utils.py` - DRS utility functions
- `shared/account_utils.py` - Account management utilities
- `shared/response_utils.py` - API response formatting
- `shared/instance_matcher.py` - Instance matching logic (NEW)
- `shared/drs_client.py` - DRS client wrapper (NEW)
- `shared/drs_job_monitor.py` - Job monitoring (NEW)

## Deployment Order

1. **Phase 1**: Deploy DynamoDB tables and data models
2. **Phase 2-4**: Deploy shared modules (instance matcher, DRS client, job monitor)
3. **Phase 5**: Deploy data-management-handler updates and API Gateway configuration endpoints
4. **Phase 6**: Deploy execution-handler updates and API Gateway execution endpoints
5. **Phase 7**: Deploy query-handler updates and API Gateway query endpoints
6. **Phase 8**: Complete testing and documentation
7. **Phase 9**: Production rollout

## Success Criteria

- [ ] All 104 tests passing
- [ ] Failover RTO < 30 minutes
- [ ] Failback RTO < 30 minutes
- [ ] Instance matching accuracy > 99%
- [ ] Private IP preservation rate = 100%
- [ ] Zero data loss during failover/failback
- [ ] API response time < 2 seconds
- [ ] Documentation complete and reviewed
- [ ] Performance benchmarks documented
- [ ] Production deployment successful

## Risk Mitigation

### High-Risk Tasks
- **Instance Matching**: Complex logic with multiple validation rules
  - Mitigation: Extensive unit tests, integration tests with real AWS accounts
  
- **Private IP Preservation**: Critical for application connectivity
  - Mitigation: Validation before failback, clear error messages, rollback capability
  
- **Agent Installation**: Network connectivity and permissions required
  - Mitigation: Prerequisite validation, retry logic, detailed error logging
  
- **Cross-Account Operations**: IAM role assumption can fail
  - Mitigation: Credential caching, error handling, external ID validation

- **Handler Integration**: Risk of breaking existing functionality
  - Mitigation: Comprehensive unit tests, integration tests, gradual rollout

### Medium-Risk Tasks
- **DRS API Rate Limiting**: High-volume operations may hit limits
  - Mitigation: Exponential backoff, batch operations, monitoring
  
- **CloudFormation Updates**: Risk of stack update failures
  - Mitigation: Validate templates, test in dev first, rollback plan

## Notes

- All tasks should be completed in order within each phase
- Unit tests should be written alongside implementation
- Integration tests should be written after component completion
- E2E tests should be written after all components are integrated
- Documentation should be updated continuously throughout implementation
- **CRITICAL**: Integration into existing handlers requires careful testing to avoid breaking existing functionality
- **Dual Invocation Pattern**: All handlers must support both API Gateway and Direct Lambda invocation
- **Shared Modules**: All three handlers will use the same shared modules for consistency
- **DynamoDB Schema**: Extend existing tables where possible, create new tables only when necessary
- **API Gateway**: Add new resources and methods to existing stacks, maintain consistent naming
- **EventBridge**: Extend existing polling rule rather than creating new rules
- **Step Functions**: Integrate with existing state machine for wave-based orchestration
- **Performance**: Target RTO <30 minutes for 100 instances (88-92% improvement vs standard DRS)
- **Testing**: Comprehensive test coverage (59 unit + 37 integration + 8 E2E = 104 tests)
- **Monitoring**: CloudWatch dashboard, alarms, and Logs Insights queries for observability
