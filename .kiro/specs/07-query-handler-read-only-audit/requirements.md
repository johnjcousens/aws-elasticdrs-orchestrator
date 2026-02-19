# Query Handler Read-Only Audit - Requirements

## Overview

The query-handler Lambda function (7248 lines) is performing sync operations that violate its read-only design principle. This spec audits all sync operations and provides a refactoring plan to move them to the appropriate handlers while maintaining clean architecture and avoiding Lambda size constraints.

## Problem Statement

### Current Handler Responsibilities (Intended)
```
data-management-handler: CRUD Operations + Data Sync
  - Protection Groups, Recovery Plans
  - Tag sync, Launch configs
  - Recovery instance sync
  - Source server inventory sync
  - Staging account sync

execution-handler: Recovery Actions
  - Start recovery, Cancel execution
  - Terminate instances, Apply configs
  - Wave completion sync

query-handler: Read Operations ONLY
  - List executions, Poll DRS jobs
  - Server status, Dashboard data
  - NO WRITES, NO SYNC OPERATIONS
```

### Violations Discovered

**query-handler is performing sync operations (VIOLATES READ-ONLY):**

1. **`poll_wave_status()` (lines 2588-2900+)**
   - Updates execution history table with wave completion status
   - Updates cancellation status
   - Updates pause states
   - Writes to DynamoDB: `get_execution_history_table().update_item()`

2. **`handle_sync_source_server_inventory()` (lines 5631-6100)**
   - Full DynamoDB sync operation
   - Batch writes to inventory table
   - Batch writes to region status table
   - Deletes stale records
   - Queries DRS/EC2 APIs across all accounts/regions
   - Writes to DynamoDB: `inventory_table.batch_writer()`, `region_status_table.batch_writer()`, `inventory_table.delete_item()`

3. **`handle_sync_staging_accounts()` (lines 5417-5630)**
   - Auto-extends DRS servers from staging to target accounts
   - Calls `auto_extend_staging_servers()` which performs DRS API writes
   - Writes to DRS: `extend_source_server()` (DRS API write operation)

### Architecture Concerns

**Handler Sizes:**
- query-handler: 7248 lines
- data-management-handler: 9867 lines
- Total if consolidated: ~17,115 lines

**Constraints:**
- Lambda deployment package: 250MB uncompressed, 50MB zipped
- CloudFormation template: 1MB limit
- Need clean separation of concerns
- Avoid making one Lambda too large

## User Stories

### 1. Clean Handler Separation
**As a** developer  
**I want** query-handler to be strictly read-only  
**So that** the architecture follows single responsibility principle and is easier to maintain

**Acceptance Criteria:**
- query-handler performs ZERO DynamoDB writes
- query-handler performs ZERO DRS API writes
- All sync operations moved to appropriate handlers
- Handler responsibilities clearly documented
- IAM principal extraction works for direct Lambda invocations
- Audit logs capture both API Gateway and direct Lambda invocations

### 2. Inventory Sync in Data Management
**As a** system operator  
**I want** source server inventory sync to be part of data-management-handler  
**So that** it's consistent with other data sync operations (tag sync, recovery instance sync)

**Acceptance Criteria:**
- `handle_sync_source_server_inventory()` moved to data-management-handler
- EventBridge routes directly to data-management-handler
- No cross-handler Lambda invocations needed
- Consistent with existing tag sync pattern

### 3. Staging Account Sync in Data Management
**As a** system operator  
**I want** staging account sync to be part of data-management-handler  
**So that** it's consistent with other account management operations

**Acceptance Criteria:**
- `handle_sync_staging_accounts()` moved to data-management-handler
- `auto_extend_staging_servers()` moved to shared utility or data-management-handler
- EventBridge routes directly to data-management-handler
- No cross-handler Lambda invocations needed

### 4. Wave Status Polling in Execution Handler
**As a** system operator  
**I want** wave status polling to be part of execution-handler  
**So that** it's consistent with other recovery action operations

**Acceptance Criteria:**
- `poll_wave_status()` execution history updates moved to execution-handler
- Wave completion sync is part of recovery actions
- Step Functions invoke execution-handler for wave polling
- Consistent with "wave completion sync" responsibility

### 5. Maintainable Lambda Sizes
**As a** developer  
**I want** Lambda functions to remain under size constraints  
**So that** deployments are fast and CloudFormation templates stay under limits

**Acceptance Criteria:**
- No single Lambda exceeds 15,000 lines
- Deployment packages stay under 200MB uncompressed
- CloudFormation template stays under 800KB
- Shared utilities extracted where appropriate

### 6. Dual Invocation Mode Audit Logging
**As a** security auditor  
**I want** audit logs to capture both API Gateway (Cognito) and direct Lambda (IAM) invocations  
**So that** I can track all access patterns and maintain compliance

**Acceptance Criteria:**
- Audit logs include IAM principal details for direct Lambda invocations
- Audit logs include Cognito user details for API Gateway invocations
- Audit logs distinguish between invocation modes (API_GATEWAY vs DIRECT_LAMBDA)
- Sensitive parameters are masked in audit logs
- Audit log schema includes principal_type, principal_arn, session_name fields

### 7. RBAC Permission Enforcement
**As a** system administrator  
**I want** all query operations to enforce RBAC permissions  
**So that** users can only access data they're authorized to view

**Acceptance Criteria:**
- All query operations use rbac_middleware decorators
- Permission-to-operation mapping is documented
- Auditor role has read-only access to audit logs
- Viewer role has read-only access to operational data
- Admin role has full access to all operations

## Functional Requirements

### FR1: Audit All Sync Operations
**Priority:** High  
**Description:** Identify all operations in query-handler that perform writes (DynamoDB, DRS API, etc.)

**Requirements:**
- FR1.1: Document all DynamoDB write operations
- FR1.2: Document all DRS API write operations
- FR1.3: Document all cross-service write operations
- FR1.4: Categorize each operation by appropriate handler

### FR2: Move Inventory Sync to Data Management
**Priority:** High  
**Description:** Move source server inventory sync to data-management-handler

**Requirements:**
- FR2.1: Move `handle_sync_source_server_inventory()` to data-management-handler
- FR2.2: Update EventBridge rule to target data-management-handler
- FR2.3: Update CloudFormation template for EventBridge routing
- FR2.4: Remove function from query-handler
- FR2.5: Update API Gateway routes if needed

### FR3: Move Staging Account Sync to Data Management
**Priority:** High  
**Description:** Move staging account sync to data-management-handler

**Requirements:**
- FR3.1: Move `handle_sync_staging_accounts()` to data-management-handler
- FR3.2: Move `auto_extend_staging_servers()` to shared utility or data-management-handler
- FR3.3: Update EventBridge rule to target data-management-handler
- FR3.4: Update CloudFormation template for EventBridge routing
- FR3.5: Remove functions from query-handler
- FR3.6: Update API Gateway routes if needed

### FR4: Move Wave Status Updates to Execution Handler
**Priority:** High  
**Description:** Move wave status polling DynamoDB updates to execution-handler

**Requirements:**
- FR4.1: Analyze `poll_wave_status()` to separate read vs write operations
- FR4.2: Keep read operations in query-handler (DRS job status queries)
- FR4.3: Move execution history updates to execution-handler
- FR4.4: Update Step Functions state machine to invoke execution-handler for updates
- FR4.5: Ensure no data loss during transition

### FR5: Maintain Lambda Size Constraints
**Priority:** High  
**Description:** Ensure all Lambda functions stay under size limits

**Requirements:**
- FR5.1: Measure current deployment package sizes
- FR5.2: Estimate sizes after refactoring
- FR5.3: Extract shared utilities if needed
- FR5.4: Document final sizes and headroom

## Non-Functional Requirements

### NFR1: Zero Downtime Migration
**Priority:** High  
**Description:** Refactoring must not cause service interruption

**Requirements:**
- NFR1.1: Deploy new handlers before removing old code
- NFR1.2: Update EventBridge rules atomically
- NFR1.3: Test all sync operations after migration
- NFR1.4: Rollback plan documented

### NFR2: Performance Parity
**Priority:** High  
**Description:** Sync operations must maintain current performance

**Requirements:**
- NFR2.1: No additional Lambda cold starts
- NFR2.2: No additional cross-handler invocations
- NFR2.3: EventBridge direct invocation (no routing overhead)
- NFR2.4: Maintain current concurrency limits

### NFR3: Code Maintainability
**Priority:** High  
**Description:** Code must be easier to maintain after refactoring

**Requirements:**
- NFR3.1: Clear handler responsibilities documented
- NFR3.2: Shared utilities extracted where appropriate
- NFR3.3: Consistent patterns across handlers
- NFR3.4: Reduced code duplication

## Out of Scope

- Rewriting sync logic (only moving existing code)
- Optimizing sync performance (separate effort)
- Adding new sync operations
- Changing EventBridge schedules
- Modifying DynamoDB table schemas

## Success Criteria

1. **Zero Sync Operations in Query Handler**
   - query-handler performs ZERO DynamoDB writes
   - query-handler performs ZERO DRS API writes
   - All read operations remain in query-handler

2. **Clean Handler Separation**
   - data-management-handler: All data sync operations
   - execution-handler: All recovery action operations
   - query-handler: All read-only operations

3. **Size Constraints Met**
   - All Lambda functions < 15,000 lines
   - All deployment packages < 200MB uncompressed
   - CloudFormation template < 800KB

4. **Zero Regressions**
   - All sync operations work after migration
   - No performance degradation
   - No data loss
   - All tests pass

## Dependencies

- Existing recovery-instance-sync spec (already updated)
- CloudFormation template updates
- EventBridge rule updates
- API Gateway route updates (if needed)
- Step Functions state machine updates (for wave polling)

## Risks and Mitigations

### Risk 1: Lambda Size Exceeds Limits
**Likelihood:** Medium  
**Impact:** High  
**Mitigation:** Extract shared utilities, measure sizes before/after

### Risk 2: EventBridge Routing Breaks
**Likelihood:** Low  
**Impact:** High  
**Mitigation:** Test EventBridge rules in dev environment first, rollback plan

### Risk 3: Data Loss During Migration
**Likelihood:** Low  
**Impact:** Critical  
**Mitigation:** Deploy new handlers first, test thoroughly, gradual cutover

### Risk 4: Step Functions State Machine Breaks
**Likelihood:** Medium  
**Impact:** High  
**Mitigation:** Update state machine definition, test wave polling thoroughly

## Existing Shared Utilities (Discovered)

The codebase already has 18 shared utility modules in `lambda/shared/` that will be leveraged during refactoring:

### Core Utilities (Already Exist)

**`drs_utils.py` (1,172 lines)** - DRS API normalization and operations
- `normalize_drs_response()` - Convert PascalCase to camelCase at AWS API boundaries
- `extract_recovery_instance_details()` - Extract normalized instance data
- `batch_describe_ec2_instances()` - Efficient EC2 instance queries with batching
- `enrich_server_data()` - Enrich servers with DRS and EC2 details
- `drs_api_call_with_backoff()` - Rate-limited DRS API calls with exponential backoff
- `transform_drs_server_for_frontend()` - Transform raw DRS server to frontend format
- **Usage**: All sync operations already use these functions for DRS API calls

**`cross_account.py`** - Cross-account IAM role assumption (hub-and-spoke pattern)
- `determine_target_account_context()` - Determine target account from recovery plan
- `create_drs_client()` - Create DRS client with optional cross-account assumption
- `create_ec2_client()` - Create EC2 client with optional cross-account assumption
- `get_cross_account_session()` - Assume cross-account IAM role via STS
- **Usage**: Inventory sync and staging sync already use these for cross-account access

**`account_utils.py`** - Account validation and management
- `construct_role_arn()` - Build standardized role ARN from account ID
- `validate_account_id()` - Validate 12-digit account ID format
- `get_target_accounts()` - List all configured target accounts from DynamoDB
- `validate_target_account()` - Validate account access and permissions
- **Usage**: All account operations already use these functions

**`execution_utils.py`** - Execution state management
- `can_terminate_execution()` - Determine if execution can be terminated
- `normalize_wave_status()` - Normalize wave status to lowercase
- `get_execution_progress()` - Calculate progress metrics for dashboard
- **Usage**: Wave polling already uses `normalize_wave_status()`

**`response_utils.py`** - API Gateway response formatting
- `response()` - API Gateway response with CORS and security headers
- `error_response()` - Standardized error response for direct invocations
- `DecimalEncoder` - JSON encoder for DynamoDB Decimal types
- **Usage**: All API operations already use these functions

**`security_utils.py`** - Input validation and sanitization
- `sanitize_string()` - Remove dangerous characters with performance optimization
- `validate_drs_server_id()` - Validate DRS server ID format (s-[a-f0-9]{17})
- `validate_aws_account_id()` - Validate 12-digit account ID
- `sanitize_dynamodb_input()` - Sanitize data before DynamoDB write
- **Usage**: All input operations already use these functions

**`notifications.py`** - SNS notifications for execution lifecycle
- `send_execution_started()`, `send_execution_completed()`, `send_execution_failed()`
- `send_wave_completed()`, `send_wave_failed()`
- `publish_recovery_plan_notification()` - Publish plan-scoped notifications
- **Usage**: Non-blocking notifications for all major operations

### Supporting Utilities (Already Exist)

- `drs_regions.py` - Centralized list of DRS-available regions
- `drs_limits.py` - DRS service limits and quotas
- `iam_utils.py` - IAM role and permission utilities
- `rbac_middleware.py` - Role-based access control
- `launch_config_service.py` - Launch configuration management
- `launch_config_validation.py` - Launch config validation
- `conflict_detection.py` (1,172 lines) - Conflict detection logic
- `config_merge.py` - Configuration merging utilities
- `staging_account_models.py` - Staging account data models

### Key Patterns (Already Established)

**Data Format Convention:**
- All data uses camelCase (DynamoDB storage and API responses)
- AWS API responses normalized to camelCase at boundaries using `normalize_drs_response()`
- NO snake_case fallback patterns - data must be in correct format

**Cross-Account Pattern:**
- Hub-and-Spoke: Hub assumes IAM role in spoke accounts via STS
- `determine_target_account_context()` extracts account from recovery plan
- `create_drs_client()` handles optional cross-account assumption

**DynamoDB Pattern:**
- Lazy initialization: Resources initialized on first use
- Decimal handling: Automatic conversion via `DecimalEncoder`

**Validation Pattern:**
- Comprehensive input validation at entry points
- Sanitization with performance optimizations (skip safe strings)

### Refactoring Impact

**No New Utilities Needed**: All sync operations already use existing shared utilities:
- Inventory sync: Uses `drs_utils`, `cross_account`, `account_utils`
- Staging sync: Uses `staging_account_models`, `drs_utils`, `cross_account`
- Wave polling: Uses `execution_utils`, `drs_utils`

**Implementation Strategy**: Move sync operations to appropriate handlers while maintaining existing utility imports. No utility extraction phase needed.

## Open Questions

1. ~~Should `poll_wave_status()` be split into read (query-handler) and write (execution-handler) operations?~~ **ANSWERED: Yes, split function**
2. ~~Should shared utilities be extracted to `lambda/shared/` or kept in handlers?~~ **ANSWERED: Already exist - leverage existing utilities**
3. ~~Should we consolidate query-handler into data-management-handler entirely?~~ **ANSWERED: No, keep separate with shared utilities**
4. What is the current deployment package size for each handler? **ACTION: Measure after Phase 1**
5. Should inventory sync utilities be extracted to `lambda/shared/inventory_utils.py`? **ACTION: Evaluate during implementation**
6. Should staging account sync utilities be extracted to `lambda/shared/staging_utils.py`? **ACTION: Evaluate during implementation (staging_account_models.py already exists)**

## References

- Handler Responsibility Pattern (from user)
- Recovery Instance Sync Spec: `.kiro/specs/recovery-instance-sync/`
- Lambda Size Limits: https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html
- CloudFormation Limits: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/cloudformation-limits.html
