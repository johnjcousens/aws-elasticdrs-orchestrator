# Recovery Instance Sync - Implementation Tasks

## Overview

This task list implements the Recovery Instance Sync feature to reduce Recovery Plans page load time from 20+ seconds to under 3 seconds by caching recovery instance data in DynamoDB.

## Task List

### Phase 1: Infrastructure Setup

- [~] 1. Create DynamoDB Cache Table in CloudFormation
  - [~] 1.1 Add RecoveryInstancesCacheTable to database-stack.yaml
  - [~] 1.2 Add table outputs (name and ARN) to database-stack.yaml
  - [~] 1.3 Update master-template.yaml to pass table name to nested stacks

- [~] 2. Create Background Sync Lambda Function
  - [~] 2.1 Create lambda/recovery-instance-sync/ directory structure
  - [~] 2.2 Implement lambda_handler() for background sync
  - [~] 2.3 Implement get_recovery_instances_for_region()
  - [~] 2.4 Implement enrich_with_ec2_details()
  - [~] 2.5 Implement find_source_execution()
  - [~] 2.6 Add error handling and logging

- [~] 3. Create EventBridge Scheduled Rule
  - [~] 3.1 Add RecoveryInstanceSyncScheduleRule to eventbridge-stack.yaml
  - [~] 3.2 Add Lambda permission for EventBridge invocation
  - [~] 3.3 Configure 5-minute schedule expression

- [~] 4. Update IAM Permissions
  - [~] 4.1 Verify unified orchestration role has DynamoDB permissions
  - [~] 4.2 Verify unified orchestration role has DRS permissions
  - [~] 4.3 Verify unified orchestration role has EC2 permissions

### Phase 2: Wave Completion Sync

- [~] 5. Implement Wave Completion Sync in Execution Handler
  - [~] 5.1 Create sync_recovery_instances_after_wave() function
  - [~] 5.2 Query DRS for recovery instances by source server IDs
  - [~] 5.3 Enrich instances with EC2 details
  - [~] 5.4 Write enriched data to DynamoDB cache
  - [~] 5.5 Add error handling (don't block wave completion)
  - [~] 5.6 Integrate into execute_wave() after wave completes

### Phase 3: Cache Query Optimization

- [~] 6. Update Data Management Handler for Cache Queries
  - [~] 6.1 Refactor checkExistingRecoveryInstances() to query cache
  - [~] 6.2 Implement batch get from DynamoDB
  - [~] 6.3 Transform cache data to expected response format
  - [~] 6.4 Add cache miss logging
  - [~] 6.5 Maintain backward compatibility with API response

- [~] 7. Optimize Terminate Recovery Instances
  - [~] 7.1 Update terminateRecoveryInstances() to query cache
  - [~] 7.2 Implement Scan with FilterExpression on sourceExecutionId
  - [~] 7.3 Group instances by region for batch termination
  - [~] 7.4 Delete cache records after successful termination
  - [~] 7.5 Add error handling for partial failures

### Phase 4: Testing

- [~] 8. Write Unit Tests for Background Sync
  - [~] 8.1 Test wave completion sync writes to DynamoDB
  - [~] 8.2 Test background sync queries all regions
  - [~] 8.3 Test cache query returns correct format
  - [~] 8.4 Test error handling for API failures
  - [~] 8.5 Test cross-account role assumption
  - [~] 8.6 Test data enrichment logic
  - [~] 8.7 Test terminate instances cache query and deletion

- [~] 9. Write Integration Tests
  - [~] 9.1 Test end-to-end wave completion sync
  - [~] 9.2 Test background sync with real DynamoDB
  - [~] 9.3 Test cache query performance (<3 seconds)
  - [~] 9.4 Test multi-region sync
  - [~] 9.5 Test cross-account access
  - [~] 9.6 Test terminate instances end-to-end

- [~] 10. Write Property-Based Tests
  - [~] 10.1 Test sync idempotency property
  - [~] 10.2 Test data integrity property (all required fields present)
  - [~] 10.3 Test timestamp ordering property
  - [~] 10.4 Test region coverage property

### Phase 5: Deployment and Monitoring

- [~] 11. Deploy Infrastructure
  - [~] 11.1 Deploy DynamoDB table via CloudFormation
  - [~] 11.2 Deploy background sync Lambda
  - [~] 11.3 Deploy EventBridge rule
  - [~] 11.4 Verify background sync runs successfully

- [ ] 12. Enable Wave Completion Sync
  - [ ] 12.1 Deploy execution handler with sync logic
  - [ ] 12.2 Test with single wave execution
  - [ ] 12.3 Verify data written to cache

- [ ] 13. Enable Cache Queries
  - [ ] 13.1 Deploy data management handler with cache queries
  - [ ] 13.2 Test Recovery Plans page load time
  - [ ] 13.3 Monitor for cache misses

- [ ] 14. Setup Monitoring and Alarms
  - [ ] 14.1 Create CloudWatch dashboard for cache metrics
  - [ ] 14.2 Create alarm for background sync errors
  - [ ] 14.3 Create alarm for DynamoDB throttling
  - [ ] 14.4 Create alarm for data management handler duration
  - [ ] 14.5 Create alarm for cache miss rate

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

### Task 2: Create Background Sync Lambda Function

**Objective**: Implement Lambda function that syncs recovery instances every 5 minutes.

**Acceptance Criteria**:
- Queries DRS describe_recovery_instances() for all active regions
- Enriches instances with EC2 details (Name, IPs, instance type, launch time)
- Finds source execution from execution history
- Writes enriched data to DynamoDB cache
- Completes within 5 minutes
- Handles errors gracefully (logs and continues)

**Implementation Notes**:
- Create new directory: `lambda/recovery-instance-sync/`
- Follow pattern from existing Lambda handlers
- Use boto3 for DRS, EC2, and DynamoDB clients
- Implement pagination for DRS API calls
- Use batch_writer for efficient DynamoDB writes

**Files to Create**:
- `lambda/recovery-instance-sync/index.py`
- `lambda/recovery-instance-sync/requirements.txt`

### Task 3: Create EventBridge Scheduled Rule

**Objective**: Configure EventBridge to trigger background sync Lambda every 5 minutes.

**Acceptance Criteria**:
- Rule triggers every 5 minutes
- Targets background sync Lambda
- Lambda permission granted for EventBridge invocation
- Rule enabled by default

**Implementation Notes**:
- Follow pattern from TagSyncScheduleRule in eventbridge-stack.yaml
- Use ScheduleExpression: `rate(5 minutes)`
- Reference EventBridgeInvokeRole for RoleArn
- Add Lambda permission resource

**Files to Modify**:
- `cfn/eventbridge-stack.yaml`

### Task 4: Update IAM Permissions

**Objective**: Verify unified orchestration role has all required permissions.

**Acceptance Criteria**:
- DynamoDB permissions cover recovery-instances table
- DRS permissions include DescribeRecoveryInstances and DescribeSourceServers
- EC2 permissions include DescribeInstances
- Cross-account role assumption supported

**Implementation Notes**:
- Existing wildcard policies should cover new table
- Verify DRS and EC2 permissions in unified role
- No new policies needed (existing patterns sufficient)

**Files to Verify**:
- `cfn/master-template.yaml` (UnifiedOrchestrationRole)

### Task 5: Implement Wave Completion Sync in Execution Handler

**Objective**: Add sync logic to execution handler that runs after wave completes.

**Acceptance Criteria**:
- Queries DRS for recovery instances by source server IDs
- Enriches with EC2 details
- Writes to DynamoDB cache
- Doesn't block wave completion on errors
- Logs sync results

**Implementation Notes**:
- Create sync_recovery_instances_after_wave() function
- Call from execute_wave() after wave status becomes COMPLETED
- Use try/except to prevent blocking wave completion
- Include replicationStagingAccountId and source infrastructure fields

**Files to Modify**:
- `lambda/execution-handler/index.py`

### Task 6: Update Data Management Handler for Cache Queries

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

### Task 7: Optimize Terminate Recovery Instances

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

### Task 8: Write Unit Tests

**Objective**: Comprehensive unit test coverage for all new functionality.

**Acceptance Criteria**:
- All functions have unit tests
- Mocks used for AWS API calls
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
- Use Hypothesis for property-based tests (max_examples=100, deadline=5000ms)
- Follow PEP 8 with 120 character line length

**Files to Create**:
- `tests/unit/test_recovery_instance_sync.py`
- `tests/unit/test_wave_completion_sync.py`
- `tests/unit/test_cache_queries.py`
- `tests/unit/test_terminate_instances_cache.py`

### Task 9: Write Integration Tests

**Objective**: End-to-end integration tests with real AWS services.

**Acceptance Criteria**:
- Tests use real DynamoDB (local or test environment)
- Wave completion sync tested end-to-end
- Background sync tested with multiple regions
- Performance validated (<3 seconds)
- Cross-account scenarios tested

**Implementation Notes**:
- Use moto for AWS service mocking
- Test with real DynamoDB Local or test environment
- Measure and assert performance targets
- Test multi-region scenarios

**Files to Create**:
- `tests/integration/test_recovery_instance_sync_integration.py`

### Task 10: Write Property-Based Tests

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

### Task 11: Deploy Infrastructure

**Objective**: Deploy DynamoDB table, Lambda, and EventBridge rule to dev environment.

**Acceptance Criteria**:
- CloudFormation stack deploys successfully
- DynamoDB table created
- Lambda function deployed
- EventBridge rule created and enabled
- Background sync runs successfully

**Implementation Notes**:
- **CRITICAL**: ALWAYS use deploy script: `./scripts/deploy.sh dev`
- **NEVER** use direct AWS CLI commands for deployment
- Deploy script runs validation, security scans, tests, and deployment
- Verify stack status in CloudFormation console
- Check Lambda logs for successful execution
- Verify DynamoDB table has data after first sync

**Commands**:
```bash
# Deploy infrastructure
./scripts/deploy.sh dev

# Verify stack status
aws cloudformation describe-stacks --stack-name hrp-drs-tech-adapter-dev

# Check Lambda logs
aws logs tail /aws/lambda/hrp-drs-tech-adapter-recovery-instance-sync-dev
```

### Task 12: Enable Wave Completion Sync

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

### Task 13: Enable Cache Queries

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

### Task 14: Setup Monitoring and Alarms

**Objective**: Create CloudWatch dashboard and alarms for monitoring.

**Acceptance Criteria**:
- Dashboard shows cache metrics
- Alarms created for critical issues
- Alarms trigger on threshold breaches
- Notifications configured

**Implementation Notes**:
- Create CloudWatch dashboard with:
  - Background sync duration
  - Cache query latency
  - Cache miss rate
  - DynamoDB throttling
- Create alarms for:
  - Background sync errors
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
