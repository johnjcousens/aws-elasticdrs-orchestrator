# Recovery Instance Sync - Implementation Tasks

## Overview

This task list implements the Recovery Instance Sync feature to reduce Recovery Plans page load time from 20+ seconds to under 3 seconds by caching recovery instance data in DynamoDB using a shared utility pattern integrated into the data-management-handler.

## Task List

### Phase 1: Infrastructure Setup

- [x] 1. Create DynamoDB Cache Table in CloudFormation
  - [x] 1.1 Add RecoveryInstancesCacheTable to database-stack.yaml
  - [x] 1.2 Add table outputs (name and ARN) to database-stack.yaml
  - [x] 1.3 Update master-template.yaml to pass table name to nested stacks

- [ ] 2. Create EventBridge Scheduled Rule for Data Management Handler
  - [ ] 2.1 Add RecoveryInstanceSyncScheduleRule to eventbridge-stack.yaml
  - [ ] 2.2 Configure rule to target data-management-handler Lambda (direct)
  - [ ] 2.3 Add event payload: {"operation": "sync_recovery_instances"}
  - [ ] 2.4 Configure 5-minute schedule expression

- [ ] 3. Update IAM Permissions for Handlers
  - [ ] 3.1 Verify data-management-handler role has DynamoDB permissions for recovery-instances table (read/write)
  - [ ] 3.2 Verify data-management-handler role has DRS permissions (DescribeRecoveryInstances, DescribeSourceServers)
  - [ ] 3.3 Verify data-management-handler role has EC2 permissions (DescribeInstances)
  - [ ] 3.4 Verify data-management-handler role has cross-account role assumption permissions
  - [ ] 3.5 Verify execution-handler role has DynamoDB write permissions for recovery-instances table
  - [ ] 3.6 Verify query-handler role has DynamoDB read-only permissions (NO writes)


### Phase 2: Shared Utility Implementation

- [ ] 4. Create Shared Utility: lambda/shared/recovery_instance_sync.py
  - [ ] 4.1 Implement sync_all_recovery_instances() - Main sync function for EventBridge trigger
  - [ ] 4.2 Implement sync_recovery_instances_for_account() - Single account/region sync
  - [ ] 4.3 Implement get_recovery_instances_for_region() - Query DRS for recovery instances
  - [ ] 4.4 Implement enrich_with_ec2_details() - Add EC2 instance details
  - [ ] 4.5 Implement find_source_execution() - Find source execution from history
  - [ ] 4.6 Implement get_recovery_instance_sync_status() - Get last sync status
  - [ ] 4.7 Add error handling and logging throughout
  - [ ] 4.8 Add DynamoDB batch write operations

### Phase 3: Data Management Handler Integration

- [ ] 5. Update Data Management Handler for EventBridge Triggers
  - [ ] 5.1 Update lambda_handler() to detect EventBridge sync events
  - [ ] 5.2 Add event detection for {"operation": "sync_recovery_instances"}
  - [ ] 5.3 Route to handle_recovery_instance_sync() function
  - [ ] 5.4 Add error handling for EventBridge invocations

- [ ] 6. Add API Gateway Endpoints for Manual Sync
  - [ ] 6.1 Add POST /drs/recovery-instance-sync endpoint routing
  - [ ] 6.2 Add GET /drs/recovery-instance-sync/status endpoint routing
  - [ ] 6.3 Implement handle_recovery_instance_sync() handler function
  - [ ] 6.4 Implement get_recovery_instance_sync_status() handler function
  - [ ] 6.5 Add request validation and error handling

- [ ] 7. Add Direct Invocation Operations
  - [ ] 7.1 Add "sync_recovery_instances" operation to handle_direct_invocation()
  - [ ] 7.2 Add "get_recovery_instance_sync_status" operation to handle_direct_invocation()
  - [ ] 7.3 Implement operation routing to shared utility functions
  - [ ] 7.4 Add response formatting for direct invocations

- [ ] 8. Implement Wave Completion Sync in Execution Handler
  - [ ] 8.1 Import recovery_instance_sync from shared utilities
  - [ ] 8.2 Create sync_recovery_instances_after_wave() function
  - [ ] 8.3 Call sync_recovery_instances_for_account() after wave completes
  - [ ] 8.4 Add error handling (don't block wave completion)
  - [ ] 8.5 Integrate into execute_wave() after wave status becomes COMPLETED

### Phase 4: Cache Query Optimization

- [ ] 9. Update Data Management Handler for Cache Queries
  - [ ] 9.1 Refactor checkExistingRecoveryInstances() to query cache
  - [ ] 9.2 Implement batch get from DynamoDB
  - [ ] 9.3 Transform cache data to expected response format
  - [ ] 9.4 Add cache miss logging
  - [ ] 9.5 Maintain backward compatibility with API response

- [ ] 10. Optimize Terminate Recovery Instances
  - [ ] 10.1 Update terminateRecoveryInstances() to query cache
  - [ ] 10.2 Implement Scan with FilterExpression on sourceExecutionId
  - [ ] 10.3 Group instances by region for batch termination
  - [ ] 10.4 Delete cache records after successful termination
  - [ ] 10.5 Add error handling for partial failures


### Phase 5: Testing

- [ ] 11. Write Unit Tests for Shared Utility
  - [ ] 11.1 Test sync_all_recovery_instances() with mocked AWS clients
  - [ ] 11.2 Test sync_recovery_instances_for_account() for single account
  - [ ] 11.3 Test get_recovery_instances_for_region() with pagination
  - [ ] 11.4 Test enrich_with_ec2_details() data transformation
  - [ ] 11.5 Test find_source_execution() lookup logic
  - [ ] 11.6 Test error handling for API failures
  - [ ] 11.7 Test cross-account role assumption

- [ ] 12. Write Unit Tests for Handler Integration
  - [ ] 12.1 Test EventBridge event detection in lambda_handler()
  - [ ] 12.2 Test API Gateway routing for sync endpoints
  - [ ] 12.3 Test direct invocation operations
  - [ ] 12.4 Test wave completion sync integration
  - [ ] 12.5 Test cache query functions
  - [ ] 12.6 Test terminate instances cache operations

- [ ] 13. Write Integration Tests
  - [ ] 13.1 Test end-to-end EventBridge-triggered sync
  - [ ] 13.2 Test end-to-end wave completion sync
  - [ ] 13.3 Test cache query performance (<3 seconds)
  - [ ] 13.4 Test multi-region sync
  - [ ] 13.5 Test cross-account access
  - [ ] 13.6 Test terminate instances end-to-end

- [ ] 14. Write Property-Based Tests
  - [ ] 14.1 Test sync idempotency property
  - [ ] 14.2 Test data integrity property (all required fields present)
  - [ ] 14.3 Test timestamp ordering property
  - [ ] 14.4 Test region coverage property


### Phase 6: Deployment and Monitoring

- [ ] 15. Deploy Infrastructure
  - [ ] 15.1 Deploy DynamoDB table via CloudFormation
  - [ ] 15.2 Deploy EventBridge rule targeting data-management-handler
  - [ ] 15.3 Verify EventBridge rule is enabled
  - [ ] 15.4 Verify IAM permissions are correct

- [ ] 16. Deploy Shared Utility and Handler Updates
  - [ ] 16.1 Deploy data-management-handler with shared utility
  - [ ] 16.2 Test EventBridge-triggered sync runs successfully
  - [ ] 16.3 Test manual sync via API endpoint
  - [ ] 16.4 Verify data written to cache

- [ ] 17. Enable Wave Completion Sync
  - [ ] 17.1 Deploy execution handler with sync logic
  - [ ] 17.2 Test with single wave execution
  - [ ] 17.3 Verify data written to cache after wave completes

- [ ] 18. Enable Cache Queries
  - [ ] 18.1 Deploy data management handler with cache queries
  - [ ] 18.2 Test Recovery Plans page load time
  - [ ] 18.3 Monitor for cache misses

- [ ] 19. Setup Monitoring and Alarms
  - [ ] 19.1 Create CloudWatch dashboard for cache metrics
  - [ ] 19.2 Create alarm for sync errors in data-management-handler
  - [ ] 19.3 Create alarm for DynamoDB throttling
  - [ ] 19.4 Create alarm for data management handler duration
  - [ ] 19.5 Create alarm for cache miss rate

## Task Details

### Task 1: Create DynamoDB Cache Table in CloudFormation

**Objective**: Add RecoveryInstancesCacheTable to database-stack.yaml following existing patterns.

**Acceptance Criteria**:
- Table uses camelCase schema convention (sourceServerId as partition key)
- BillingMode set to PAY_PER_REQUEST
- PointInTimeRecovery enabled
- SSE enabled
- Outputs added for table name and ARN

**Implementation Notes**:
- Follow pattern from existing tables in database-stack.yaml
- Use naming convention: `${ProjectName}-recovery-instances-${Environment}`
- No GSI needed (queries only by sourceServerId)
- Add replicationStagingAccountId and source infrastructure fields to schema
- Follow CloudFormation patterns: camelCase attributes, PAY_PER_REQUEST billing, PointInTimeRecovery enabled
- Use existing DynamoDB table patterns for consistency

**Files to Modify**:
- `cfn/database-stack.yaml`

### Task 2: Create EventBridge Scheduled Rule for Data Management Handler

**Objective**: Configure EventBridge to trigger data-management-handler every 5 minutes for recovery instance sync.

**Acceptance Criteria**:
- Rule triggers every 5 minutes
- Targets data-management-handler Lambda (not a separate Lambda)
- Event payload includes: {"operation": "sync_recovery_instances"}
- Lambda permission granted for EventBridge invocation
- Rule enabled by default

**Implementation Notes**:
- Follow pattern from TagSyncScheduleRule in eventbridge-stack.yaml
- Use ScheduleExpression: `rate(5 minutes)`
- Reference EventBridgeInvokeRole for RoleArn
- Target: data-management-handler Lambda ARN
- Input: {"operation": "sync_recovery_instances"}
- Add Lambda permission resource for EventBridge invocation

**Files to Modify**:
- `cfn/eventbridge-stack.yaml`

### Task 3: Update IAM Permissions for Handlers

**Objective**: Verify both handlers have appropriate permissions for their responsibilities.

**Acceptance Criteria**:
- data-management-handler has DynamoDB read/write permissions for recovery-instances table
- data-management-handler has DRS permissions (DescribeRecoveryInstances, DescribeSourceServers)
- data-management-handler has EC2 permissions (DescribeInstances)
- data-management-handler has cross-account role assumption permissions
- execution-handler has DynamoDB write permissions for recovery-instances table
- query-handler has DynamoDB read-only permissions (NO writes)

**Implementation Notes**:
- data-management-handler: Needs DRS/EC2 API calls + DynamoDB operations (performs sync operations)
- execution-handler: Needs DynamoDB writes (wave completion sync)
- query-handler: Only needs DynamoDB reads (read-only operations, NO sync)
- Existing wildcard policies should cover new table
- Verify DRS and EC2 permissions in data-management-handler role
- data-management-handler already has comprehensive permissions for CRUD operations

**Files to Verify**:
- `cfn/master-template.yaml` (UnifiedOrchestrationRole used by both handlers)

### Task 4: Create Shared Utility: lambda/shared/recovery_instance_sync.py

**Objective**: Implement shared utility module with all recovery instance sync logic.

**Acceptance Criteria**:
- sync_all_recovery_instances() queries all regions and accounts
- sync_recovery_instances_for_account() handles single account/region
- get_recovery_instances_for_region() queries DRS API with pagination
- enrich_with_ec2_details() adds EC2 instance details
- find_source_execution() finds source execution from history
- get_recovery_instance_sync_status() returns last sync status
- All functions have comprehensive error handling
- DynamoDB batch write operations implemented

**Implementation Notes**:
- Follow pattern from lambda/shared/launch_config_service.py
- Use boto3 for DRS, EC2, and DynamoDB clients
- Implement pagination for DRS API calls
- Use batch_writer for efficient DynamoDB writes
- Include replicationStagingAccountId and source infrastructure fields
- Add detailed logging for monitoring
- Handle cross-account role assumption
- Called by data-management-handler for all sync operations

**Files to Create**:
- `lambda/shared/recovery_instance_sync.py`

### Task 5: Update Data Management Handler for EventBridge Triggers

**Objective**: Update lambda_handler() to detect and handle EventBridge sync events directly.

**Acceptance Criteria**:
- lambda_handler() detects EventBridge events with {"operation": "sync_recovery_instances"}
- Calls shared utility sync_all_recovery_instances() directly
- Error handling prevents Lambda failures
- Logs EventBridge invocations

**Implementation Notes**:
- Follow existing pattern for EventBridge tag sync detection
- Check for "operation" key in event
- Call shared utility sync_all_recovery_instances() directly (no routing)
- Return success/error response
- Add to existing lambda_handler() logic (don't replace)

**Files to Modify**:
- `lambda/data-management-handler/index.py`

### Task 6: Add API Gateway Endpoints for Manual Sync

**Objective**: Add API endpoints for manual recovery instance sync and status queries handled directly by data-management-handler.

**Acceptance Criteria**:
- POST /drs/recovery-instance-sync triggers manual sync directly
- GET /drs/recovery-instance-sync/status returns last sync status directly
- Endpoints follow existing API patterns
- Request validation and error handling implemented

**Implementation Notes**:
- Add routing in handle_api_gateway_request()
- Follow pattern from existing /drs/* endpoints
- Implement handle_recovery_instance_sync() handler function
- Implement get_recovery_instance_sync_status() handler function
- Call shared utility functions directly (no routing to other handlers)
- Return standardized API responses

**Files to Modify**:
- `lambda/data-management-handler/index.py`

### Task 7: Add Direct Invocation Operations

**Objective**: Add direct invocation operations for CLI/SDK access handled directly by data-management-handler.

**Acceptance Criteria**:
- "sync_recovery_instances" operation triggers sync directly
- "get_recovery_instance_sync_status" operation returns status directly
- Operations follow existing direct invocation patterns
- Response formatting matches API Gateway responses

**Implementation Notes**:
- Add to handle_direct_invocation() function
- Follow pattern from existing operations
- Call shared utility functions directly (no routing to other handlers)
- Return standardized responses

**Files to Modify**:
- `lambda/data-management-handler/index.py`

### Task 8: Implement Wave Completion Sync in Execution Handler

**Objective**: Add sync logic to execution handler that runs after wave completes.

**Acceptance Criteria**:
- Imports recovery_instance_sync from shared utilities
- Queries DRS for recovery instances by source server IDs
- Enriches with EC2 details
- Writes to DynamoDB cache
- Doesn't block wave completion on errors
- Logs sync results

**Implementation Notes**:
- Import sync_recovery_instances_for_account from shared.recovery_instance_sync
- Create sync_recovery_instances_after_wave() function
- Call from execute_wave() after wave status becomes COMPLETED
- Use try/except to prevent blocking wave completion
- Include replicationStagingAccountId and source infrastructure fields

**Files to Modify**:
- `lambda/execution-handler/index.py`

### Task 9: Update Data Management Handler for Cache Queries

**Objective**: Refactor checkExistingRecoveryInstances() to query DynamoDB cache instead of DRS API.

**Acceptance Criteria**:
- Queries DynamoDB cache by source server IDs
- Returns data in same format as original implementation
- Completes in under 3 seconds for 100 servers
- Logs cache misses
- Maintains backward compatibility

**Implementation Notes**:
- Replace DRS/EC2 API calls with DynamoDB batch get
- Use table.get_item() for each source server ID
- Transform cache data to match original response format
- Add cache miss logging for monitoring

**Files to Modify**:
- `lambda/data-management-handler/index.py`

### Task 10: Optimize Terminate Recovery Instances

**Objective**: Update terminateRecoveryInstances() to use cache instead of expensive API calls.

**Acceptance Criteria**:
- Queries cache using Scan with FilterExpression on sourceExecutionId
- Groups instances by region for batch termination
- Deletes cache records after successful termination
- Completes in under 10 seconds for 100 instances
- Reduces DRS API calls by 100%

**Implementation Notes**:
- Use table.scan() with FilterExpression
- Group instances by region for efficient termination
- Use batch_writer for cache deletion
- Handle partial failures gracefully

**Files to Modify**:
- `lambda/data-management-handler/index.py`

### Task 11: Write Unit Tests for Shared Utility

**Objective**: Comprehensive unit test coverage for shared utility functions.

**Acceptance Criteria**:
- All shared utility functions have unit tests
- Mocks used for AWS API calls (DRS, EC2, DynamoDB)
- Error handling tested
- Edge cases covered
- Test coverage >80%

**Implementation Notes**:
- Use pytest and unittest.mock
- Mock boto3 clients (DRS, EC2, DynamoDB)
- Test happy path and error scenarios
- Follow existing test patterns
- Use virtual environment: `source .venv/bin/activate`
- Run tests with: `.venv/bin/pytest tests/unit/ -v`

**Files to Create**:
- `tests/unit/test_recovery_instance_sync_shared.py`

### Task 12: Write Unit Tests for Handler Integration

**Objective**: Unit tests for data-management-handler and execution-handler integration.

**Acceptance Criteria**:
- EventBridge event detection tested
- API Gateway routing tested
- Direct invocation operations tested
- Wave completion sync tested
- Cache query functions tested
- Terminate instances cache operations tested

**Implementation Notes**:
- Mock shared utility functions
- Test event routing logic
- Test API endpoint handlers
- Test direct invocation handlers
- Follow existing handler test patterns

**Files to Create**:
- `tests/unit/test_data_management_handler_sync.py`
- `tests/unit/test_execution_handler_sync.py`

### Task 13: Write Integration Tests

**Objective**: End-to-end integration tests with real AWS services.

**Acceptance Criteria**:
- Tests use real DynamoDB (local or test environment)
- EventBridge-triggered sync tested end-to-end
- Wave completion sync tested end-to-end
- Performance validated (<3 seconds)
- Cross-account scenarios tested

**Implementation Notes**:
- Use moto for AWS service mocking
- Test with real DynamoDB Local or test environment
- Measure and assert performance targets
- Test multi-region scenarios

**Files to Create**:
- `tests/integration/test_recovery_instance_sync_integration.py`

### Task 14: Write Property-Based Tests

**Objective**: Property-based tests to validate invariants.

**Acceptance Criteria**:
- Idempotency property tested
- Data integrity property tested
- Timestamp ordering property tested
- Region coverage property tested

**Implementation Notes**:
- Use Hypothesis for property-based testing (configured in pyproject.toml)
- Generate random but valid test data
- Test invariants that should always hold
- Follow existing property test patterns
- Configuration: max_examples=100, deadline=5000ms
- Run with: `.venv/bin/pytest tests/unit/test_recovery_instance_sync_property.py -v --hypothesis-show-statistics`

**Files to Create**:
- `tests/unit/test_recovery_instance_sync_property.py`

### Task 15: Deploy Infrastructure

**Objective**: Deploy DynamoDB table and EventBridge rule to dev environment.

**Acceptance Criteria**:
- CloudFormation stack deploys successfully
- DynamoDB table created
- EventBridge rule created and enabled
- EventBridge rule targets data-management-handler
- Background sync runs successfully

**Implementation Notes**:
- **CRITICAL**: ALWAYS use deploy script: `./scripts/deploy.sh dev`
- **NEVER** use direct AWS CLI commands for deployment
- Deploy script runs validation, security scans, tests, and deployment
- Verify stack status in CloudFormation console
- Check data-management-handler logs for successful sync execution
- Verify DynamoDB table has data after first sync

**Commands**:
```bash
# Deploy infrastructure
./scripts/deploy.sh dev

# Verify stack status
aws cloudformation describe-stacks --stack-name hrp-drs-tech-adapter-dev

# Check Lambda logs
aws logs tail /aws/lambda/hrp-drs-tech-adapter-data-management-handler-dev
```

### Task 16: Deploy Shared Utility and Handler Updates

**Objective**: Deploy data-management-handler with shared utility and sync logic.

**Acceptance Criteria**:
- Data-management-handler deployed with shared utility
- EventBridge-triggered sync runs successfully (targets data-management-handler directly)
- Manual sync via API endpoint works
- Data written to cache

**Implementation Notes**:
- Deploy with: `./scripts/deploy.sh dev --lambda-only`
- Test EventBridge trigger manually or wait for scheduled run
- Test manual sync via API: POST /drs/recovery-instance-sync
- Verify cache records created in DynamoDB
- Check data-management-handler logs (NOT query-handler logs)

**Commands**:
```bash
./scripts/deploy.sh dev --lambda-only
aws dynamodb scan --table-name hrp-drs-tech-adapter-recovery-instances-dev
```

### Task 17: Enable Wave Completion Sync

**Objective**: Deploy execution handler with wave completion sync logic.

**Acceptance Criteria**:
- Execution handler deployed with sync logic
- Wave execution triggers sync
- Data written to cache after wave completes
- No errors in Lambda logs

**Implementation Notes**:
- Deploy with: `./scripts/deploy.sh dev --lambda-only`
- Test with single wave execution
- Verify cache records created in DynamoDB
- Check execution handler logs

**Commands**:
```bash
./scripts/deploy.sh dev --lambda-only
aws dynamodb scan --table-name hrp-drs-tech-adapter-recovery-instances-dev
```

### Task 18: Enable Cache Queries

**Objective**: Deploy data management handler with cache query logic.

**Acceptance Criteria**:
- Data management handler deployed
- Recovery Plans page loads in <3 seconds
- Cache queries return correct data
- No cache miss errors (after initial sync)

**Implementation Notes**:
- Deploy with: `./scripts/deploy.sh dev --lambda-only`
- Test Recovery Plans page load time
- Monitor cache miss rate
- Verify response format matches original

**Commands**:
```bash
./scripts/deploy.sh dev --lambda-only
# Test via frontend or API
```

### Task 19: Setup Monitoring and Alarms

**Objective**: Create CloudWatch dashboard and alarms for monitoring.

**Acceptance Criteria**:
- Dashboard shows cache metrics
- Alarms created for critical issues
- Alarms trigger on threshold breaches
- Notifications configured

**Implementation Notes**:
- Create CloudWatch dashboard with:
  - Sync duration in data-management-handler
  - Cache query latency
  - Cache miss rate
  - DynamoDB throttling
- Create alarms for:
  - Sync errors in data-management-handler
  - DynamoDB throttling
  - Data management handler duration >5s
  - Cache miss rate >10%

**Files to Modify**:
- `cfn/monitoring-stack.yaml` (if exists) or add to master-template.yaml

## Dependencies

- Task 2 depends on Task 1 (Lambda needs table name)
- Task 3 depends on Task 2 (EventBridge needs Lambda ARN)
- Task 5 depends on Task 1 (Execution handler needs table)
- Task 6 depends on Task 1 (Data management handler needs table)
- Task 7 depends on Task 1 (Terminate function needs table)
- Tasks 8-10 can run in parallel
- Task 11 depends on Tasks 1-4 (infrastructure must be defined)
- Task 12 depends on Task 11 (infrastructure must be deployed)
- Task 13 depends on Task 12 (wave sync should populate cache first)
- Task 14 can run after Task 11

## Success Criteria

- [ ] Recovery Plans page loads in <3 seconds (down from 20+ seconds)
- [ ] Background sync completes in <60 seconds
- [ ] Cache miss rate <5%
- [ ] No errors in Lambda logs
- [ ] All tests passing
- [ ] CloudWatch alarms configured
- [ ] Documentation updated

## Rollback Plan

If issues occur:
1. Revert data management handler to use API calls: `./scripts/deploy.sh dev --lambda-only`
2. Keep background sync running (no harm)
3. Investigate and fix issues
4. Re-enable cache queries

## Notes

- Follow PEP 8 coding standards for all Python code
- Use camelCase for DynamoDB attribute names
- Follow existing CloudFormation patterns
- Test thoroughly before deploying to production
- Monitor cache miss rate after deployment
