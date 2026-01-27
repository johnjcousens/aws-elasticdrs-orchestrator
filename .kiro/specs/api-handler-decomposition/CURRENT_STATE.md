# API Handler Decomposition - Current State

**Last Updated**: January 23, 2026  
**Status**: Phase 2 In Progress (43% Complete)

## Summary

The API handler decomposition is 43% complete with Query Handler fully deployed and Execution Handler 62% extracted (10 of 16 functions).

## Completed Work

### Phase 0: Preparation ✅
- Shared utilities extracted (conflict_detection, drs_limits, cross_account, response_utils)
- CloudFormation templates updated for 3 new handlers
- Testing infrastructure created

### Phase 1: Query Handler ✅
- **Deployed**: aws-drs-orchestration-query-handler-dev
- **Functions**: 12 query functions (1,248 lines)
- **Endpoints**: 10 API Gateway endpoints operational
- **Tests**: 18 integration tests passing

### Phase 2: Execution Handler (In Progress)
- **Created**: lambda/execution-handler/index.py (2,552 lines, 16 functions)
- **Batch 1 Complete**: 5 core lifecycle functions
- **Batch 2 Complete**: 5 instance management functions
- **Remaining**: 2 batches (9 functions)

## Current File Sizes

| File | Lines | Functions | Status |
|------|-------|-----------|--------|
| api-handler/index.py | 11,613 | 133 | Monolithic (being decomposed) |
| execution-handler/index.py | 2,552 | 16 | 62% complete |
| query-handler/index.py | 1,248 | 12 | 100% complete |

## Execution Handler Progress

### Extracted (10 functions)
1. `execute_recovery_plan()` - Start Step Functions execution
2. `list_executions()` - Query DynamoDB with pagination
3. `get_execution_details()` - Get execution details by ID
4. `cancel_execution()` - Stop Step Functions, update DynamoDB
5. `pause_execution()` - Set pause flag
6. `resume_execution()` - Clear pause flag, send task token
7. `get_execution_details_realtime()` - Get real-time execution data
8. `terminate_recovery_instances()` - Terminate recovery instances
9. `get_recovery_instances()` - Get recovery instance details
10. `get_termination_job_status()` - Check DRS termination job progress

### Remaining (6 functions)

**Batch 3: Execution Management** (3 functions)
- `delete_executions_by_ids()` - Delete executions by ID list
- `delete_completed_executions()` - Bulk delete completed executions
- `get_job_log_items()` - Get DRS job logs for execution

**Batch 4: Helper Functions** (3 functions)
- `enrich_execution_with_server_details()` - Add server metadata
- `reconcile_wave_status_with_drs()` - Sync wave status with DRS
- `recalculate_execution_status()` - Recalculate overall status

**Note**: Additional helper functions (`get_execution_details_fast`, `get_execution_status`, `get_execution_history`) may be extracted in Batch 4 or left in api-handler as they're used by data management operations.

## Test Status

| Test Suite | Status | Count |
|------------|--------|-------|
| Unit Tests | ✅ Passing | 678 tests |
| Query Handler Integration | ✅ Passing | 18 tests |
| Execution Handler Integration | ⚠️ Not Run | 0 tests |
| E2E Tests | ⚠️ Not Run | 0 tests |

**Note**: test_conflict_detection.py has dependency issue (botocore[crt]) - excluded from test runs

## API Gateway Routing

### Query Handler (10 endpoints) ✅
- GET /drs/source-servers
- GET /drs/quotas
- GET /drs/accounts
- GET /ec2/subnets
- GET /ec2/security-groups
- GET /ec2/instance-profiles
- GET /ec2/instance-types
- GET /accounts/current
- GET /config/export
- GET /user/permissions

### Execution Handler (10 endpoints) ⚠️ Not Deployed
- POST /executions (execute recovery plan)
- GET /executions (list executions)
- GET /executions/{id} (get execution details)
- POST /executions/{id}/cancel
- POST /executions/{id}/pause
- POST /executions/{id}/resume
- GET /executions/{id}/realtime
- GET /executions/{id}/recovery-instances
- POST /executions/{id}/terminate-instances
- GET /executions/{id}/termination-status

### API Handler (28 endpoints) ⚠️ Still Monolithic
- Protection Groups (6 endpoints)
- Recovery Plans (6 endpoints)
- DRS Tag Sync (1 endpoint)
- Config Import/Export (3 endpoints)
- Target Accounts (4 endpoints)
- Execution Management (3 endpoints - to be moved)
- Job Logs (1 endpoint - to be moved)
- Execution Deletion (2 endpoints - to be moved)

## Next Steps

1. **Extract Batch 3** (3 functions): Execution management operations
2. **Extract Batch 4** (3-6 functions): Helper functions
3. **Update API Gateway**: Route execution endpoints to execution-handler
4. **Deploy Execution Handler**: Deploy to dev environment
5. **Integration Testing**: Test all 10 execution endpoints
6. **Phase 3**: Extract Data Management Handler (16 functions)

## Blockers

None currently. All dependencies resolved.

## Recent Commits

- `f207d9c` - docs: update CHANGELOG, README, and tasks.md for Batch 2 completion
- `4637aa5` - fix: update test_cross_account to mock lazy initialization functions
- `08a83bb` - feat: extract Batch 2 functions to execution handler (10/23)
- `a27d23c` - fix: add validate_server_replication_states to shared module
- `fda597c` - feat: complete Batch 1 extraction (5/5 functions)

## Key Metrics

- **Overall Progress**: 43% (10 of 23 tasks)
- **Execution Handler**: 62% (10 of 16 functions)
- **Code Reduction**: api-handler reduced from 11,613 to ~9,000 lines (estimated)
- **Test Coverage**: 678 unit tests passing
- **Deployment Status**: Query Handler live, Execution Handler pending
