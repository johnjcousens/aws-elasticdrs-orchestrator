# Requirements Document: Missing Function Migration

## Introduction

The API handler decomposition successfully extracted 3 specialized handlers (query, execution, data-management) from the monolithic API handler. However, analysis revealed that 40 critical functions were not migrated during the initial decomposition. Of these, 4 functions have since been migrated separately, leaving 36 functions requiring migration across 9 batches to complete the decomposition.

**Source**: `infra/orchestration/drs-orchestration/archive/lambda-handlers/api-handler-monolithic-20260124/index.py`

**Migration Scope**: 
- **Originally Missing**: 40 functions
- **Already Migrated**: 4 functions (ensure_default_account, get_active_executions_for_plan, get_active_execution_for_protection_group, has_circular_dependencies_by_number)
- **Remaining to Migrate**: 36 functions, ~4,174 lines of code
- **Estimated Effort**: 16 hours (2 days) across 9 batches

## Glossary

- **Monolithic_Handler**: Original api-handler at `archive/lambda-handlers/api-handler-monolithic-20260124/index.py` containing all 96 functions
- **Decomposed_Handlers**: Three specialized handlers (query-handler, execution-handler, data-management-handler)
- **Missing_Functions**: 36 functions not migrated during initial decomposition (4 already migrated separately)
- **Batch_Migration**: Grouping related functions for migration together (9 batches total)
- **Server_Enrichment**: Adding server metadata (names, IPs, recovery instances) to execution data
- **Cross_Account_Operations**: DRS operations across multiple AWS accounts using IAM role assumption
- **Conflict_Detection**: Preventing overlapping DR executions on the same servers
- **Wave_Execution**: Sequential execution of server groups during DR failover
- **Recovery_Instance**: EC2 instance created by DRS during DR failover
- **Launch_Configuration**: DRS settings controlling how recovery instances are launched
- **DRS**: AWS Elastic Disaster Recovery Service
- **Source_Server**: Server being protected by DRS replication
- **Replication_State**: Status of DRS replication (DISCONNECTED, INITIAL_SYNC, CONTINUOUS_REPLICATION, etc.)

## Requirements

### Requirement 1: Server Enrichment Functions (Batch 1 - Priority 1)

**User Story:** As a DR operator, I want to view complete server information in execution details, so that I can monitor recovery progress and troubleshoot issues.

**Functions**: 6 functions, ~840 lines (execution-handler)
- `get_server_details_map()` (Line 5299)
- `get_recovery_instances_for_wave()` (Line 5473)
- `enrich_execution_with_server_details()` (Line 5616)
- `reconcile_wave_status_with_drs()` (Line 5720)
- `recalculate_execution_status()` (Line 5912)
- `get_execution_details_realtime()` (Line 6067)

#### Acceptance Criteria

1. WHEN viewing execution details, THE System SHALL display server names from EC2 Name tags
2. WHEN viewing execution details, THE System SHALL display server IP addresses
3. WHEN viewing execution details, THE System SHALL display recovery instance details
4. WHEN viewing execution details, THE System SHALL display wave-to-server mappings
5. WHEN viewing execution details, THE System SHALL reconcile wave status with real-time DRS data
6. WHEN viewing execution details, THE System SHALL recalculate overall execution status from wave statuses
7. WHEN enriching execution data, THE System SHALL handle missing or incomplete server data gracefully

### Requirement 2: Cross-Account Support (Batch 2 - Priority 2)

**User Story:** As a DR operator, I want to perform DR operations across multiple AWS accounts, so that I can manage multi-account DR scenarios.

**Functions**: 2 functions, ~295 lines (shared/cross_account.py)
- `determine_target_account_context()` (Line 202)
- `create_drs_client()` (Line 354)

#### Acceptance Criteria

1. WHEN performing DRS operations, THE System SHALL determine target account context from request parameters
2. WHEN creating DRS clients, THE System SHALL assume cross-account IAM roles if target account specified
3. WHEN cross-account operations fail, THE System SHALL return descriptive error messages with troubleshooting guidance
4. WHEN no target account specified, THE System SHALL default to current account
5. WHEN IAM role assumption fails, THE System SHALL log detailed error information
6. WHEN all handlers create DRS clients, THE System SHALL use the shared `create_drs_client()` function

### Requirement 3: Conflict Detection (Batch 3 - Priority 3)

**User Story:** As a DR operator, I want the system to prevent conflicting DR executions, so that I avoid data corruption and execution failures.

**Functions**: 7 functions, ~545 lines (shared/conflict_detection.py)
- `get_servers_in_active_drs_jobs()` (Line 501)
- `get_all_active_executions()` (Line 662)
- `get_servers_in_active_executions()` (Line 708)
- `resolve_pg_servers_for_conflict_check()` (Line 807)
- `check_server_conflicts()` (Line 874)
- `get_plans_with_conflicts()` (Line 1002)
- `has_circular_dependencies()` (Line 9133)

#### Acceptance Criteria

1. WHEN creating protection groups, THE System SHALL check for server conflicts with active executions
2. WHEN starting DR executions, THE System SHALL check for server conflicts with active DRS jobs
3. WHEN starting DR executions, THE System SHALL check for server conflicts with other active executions
4. WHEN creating recovery plans, THE System SHALL detect circular dependencies in wave ordering
5. WHEN conflicts detected, THE System SHALL return error with list of conflicting resources
6. WHEN no conflicts detected, THE System SHALL allow operation to proceed
7. WHEN checking conflicts, THE System SHALL query both DynamoDB execution records AND live DRS job status

### Requirement 4: Wave Execution Functions (Batch 4 - Priority 4)

**User Story:** As a DR operator, I want wave-based execution with proper initialization and retry logic, so that DR failover succeeds reliably.

**Functions**: 4 functions, ~710 lines (execution-handler)
- `check_existing_recovery_instances()` (Line 3721)
- `initiate_wave()` (Line 4670)
- `get_server_launch_configurations()` (Line 4785)
- `start_drs_recovery_with_retry()` (Line 5062)

#### Acceptance Criteria

1. WHEN starting wave execution, THE System SHALL check for existing recovery instances
2. WHEN initiating wave, THE System SHALL create DRS recovery jobs for all servers in wave
3. WHEN starting DRS recovery, THE System SHALL retrieve launch configurations for all servers
4. WHEN DRS API calls fail, THE System SHALL retry with exponential backoff
5. WHEN retry limit exceeded, THE System SHALL mark wave as failed with error details
6. WHEN existing recovery instances found, THE System SHALL prevent duplicate instance creation

### Requirement 5: Recovery Instance Management (Batch 5 - Priority 5)

**User Story:** As a DR operator, I want to track recovery instance termination and apply launch configurations, so that I can manage DR infrastructure lifecycle.

**Functions**: 2 functions, ~600 lines (execution-handler)
- `get_termination_job_status()` (Line 7666)
- `apply_launch_config_to_servers()` (Line 10068)

#### Acceptance Criteria

1. WHEN terminating recovery instances, THE System SHALL track termination job status
2. WHEN termination job completes, THE System SHALL update execution status
3. WHEN applying launch configurations, THE System SHALL update DRS settings for all servers
4. WHEN launch configuration fails, THE System SHALL return error with affected servers
5. WHEN termination job is in progress, THE System SHALL return current progress percentage

### Requirement 6: Validation Functions (Batch 6 - Priority 6)

**User Story:** As a DR operator, I want server validation before DR operations, so that I avoid failures due to invalid server states.

**Functions**: 4 functions, ~255 lines (data-management-handler)
- `validate_server_replication_states()` (Line 1321)
- `validate_server_assignments()` (Line 8681)
- `validate_servers_exist_in_drs()` (Line 8721)
- `validate_and_get_source_servers()` (Line 8980)

#### Acceptance Criteria

1. WHEN creating protection groups, THE System SHALL validate server replication states
2. WHEN assigning servers, THE System SHALL validate servers exist in DRS
3. WHEN assigning servers, THE System SHALL validate server assignments are valid
4. WHEN validation fails, THE System SHALL return error with list of invalid servers
5. WHEN validation succeeds, THE System SHALL allow operation to proceed
6. WHEN checking replication states, THE System SHALL verify servers are in CONTINUOUS_REPLICATION state

### Requirement 7: Query Functions (Batch 7 - Priority 7)

**User Story:** As a DR operator, I want to query servers by tags and view protection group details, so that I can discover and manage DR-protected resources.

**Functions**: 4 functions, ~355 lines (query-handler)
- `query_drs_servers_by_tags()` (Line 2102)
- `get_protection_group_servers()` (Line 8580)
- `get_drs_source_server_details()` (Line 9010)
- `validate_target_account()` (Line 9773)

#### Acceptance Criteria

1. WHEN querying by tags, THE System SHALL return servers matching all specified tags (AND logic)
2. WHEN viewing protection group, THE System SHALL return list of servers in group
3. WHEN querying server details, THE System SHALL return DRS source server information
4. WHEN validating target account, THE System SHALL check account exists in configuration
5. WHEN tag query returns no results, THE System SHALL return empty list (not error)

### Requirement 8: Execution Cleanup (Batch 8 - Priority 8)

**User Story:** As a DR operator, I want to delete old completed executions, so that I can manage DynamoDB storage costs.

**Functions**: 2 functions, ~275 lines (execution-handler)
- `delete_completed_executions()` (Line 7826)
- `delete_executions_by_ids()` (Line 8007)

#### Acceptance Criteria

1. WHEN deleting completed executions, THE System SHALL remove executions older than specified age
2. WHEN bulk deleting executions, THE System SHALL delete all executions in provided ID list
3. WHEN deleting executions, THE System SHALL preserve active executions
4. WHEN deletion fails, THE System SHALL return error with list of failed deletions
5. WHEN deleting executions, THE System SHALL verify execution status before deletion

### Requirement 9: Import/Export Functions (Batch 9 - Priority 9)

**User Story:** As a DR operator, I want to export and import DR configuration, so that I can backup and migrate DR setups.

**Functions**: 5 functions, ~299 lines (data-management-handler)
- `export_configuration()` (Line 10511)
- `import_configuration()` (Line 10630)
- `_get_existing_protection_groups()` (Line 10770)
- `_get_existing_recovery_plans()` (Line 10782)
- `_get_active_execution_servers()` (Line 10794)

#### Acceptance Criteria

1. WHEN exporting configuration, THE System SHALL include all protection groups and recovery plans
2. WHEN importing configuration, THE System SHALL validate against existing resources
3. WHEN importing configuration, THE System SHALL check for conflicts with active executions
4. WHEN import validation fails, THE System SHALL return error with list of conflicts
5. WHEN import succeeds, THE System SHALL create all protection groups and recovery plans
6. WHEN exporting configuration, THE System SHALL return JSON format compatible with import

### Requirement 10: Migration Process

**User Story:** As a developer, I want a systematic migration process, so that I can migrate functions safely without breaking existing functionality.

#### Acceptance Criteria

1. WHEN migrating functions, THE System SHALL extract functions from monolithic handler at specified line numbers
2. WHEN migrating functions, THE System SHALL preserve all comments and code style exactly as-is
3. WHEN migrating functions, THE System SHALL maintain original function signatures without modification
4. WHEN migrating functions, THE System SHALL test after each batch completion
5. WHEN migrating functions, THE System SHALL deploy after each batch completion
6. WHEN migration complete, THE System SHALL pass all existing tests (800+ tests)
7. WHEN migration complete, THE System SHALL have no regressions in existing functionality
8. WHEN migrating to shared modules, THE System SHALL update all handlers to import from shared location
9. WHEN batch migration fails, THE System SHALL rollback changes and document failure reason

### Requirement 11: Testing and Validation

**User Story:** As a developer, I want comprehensive testing for migrated functions, so that I can ensure correctness and prevent regressions.

#### Acceptance Criteria

1. WHEN running unit tests, THE System SHALL pass all existing tests without modification
2. WHEN running integration tests, THE System SHALL pass all handler-specific tests
3. WHEN running E2E tests, THE System SHALL pass complete DR workflow tests
4. WHEN testing execution details, THE System SHALL display complete server information
5. WHEN testing wave execution, THE System SHALL complete end-to-end successfully
6. WHEN testing conflict detection, THE System SHALL prevent invalid operations
7. WHEN testing cross-account operations, THE System SHALL successfully assume roles and perform operations
8. WHEN testing import/export, THE System SHALL successfully backup and restore configuration

### Requirement 12: Completion Criteria

**User Story:** As a project manager, I want clear completion criteria, so that I can verify the migration is complete and successful.

#### Acceptance Criteria

1. WHEN all 9 batches complete, THE System SHALL have migrated all 36 functions
2. WHEN all batches complete, THE System SHALL pass all 800+ tests
3. WHEN viewing execution details page, THE System SHALL display server names, IPs, and recovery instances
4. WHEN starting DR execution, THE System SHALL initialize waves and create DRS jobs
5. WHEN creating protection groups, THE System SHALL detect and prevent conflicts
6. WHEN performing cross-account operations, THE System SHALL successfully assume roles
7. WHEN exporting configuration, THE System SHALL generate valid JSON
8. WHEN importing configuration, THE System SHALL validate and create resources
9. WHEN terminating instances, THE System SHALL track termination progress
10. WHEN deleting executions, THE System SHALL clean up old records
11. WHEN all manual tests pass, THE System SHALL be ready for production deployment
