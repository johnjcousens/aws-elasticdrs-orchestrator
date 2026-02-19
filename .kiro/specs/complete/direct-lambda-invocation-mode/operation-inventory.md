# Operation Inventory

**Date**: January 31, 2026  
**Purpose**: Comprehensive mapping of frontend features to Lambda operations for direct invocation mode

## Executive Summary

- **Total frontend features**: 45
- **Total Lambda operations needed**: 52
- **Currently implemented**: 37 (71%)
- **Missing**: 15 (29%)
- **Critical gaps**: 11 operations blocking core functionality
- **High priority gaps**: 4 operations limiting functionality

### Coverage by Handler

| Handler | Implemented | Missing | Coverage |
|---------|-------------|---------|----------|
| Query Handler | 16 | 11 | 59% |
| Data Management Handler | 18 | 7 | 72% |
| Execution Handler | 3 | 6 | 33% |
| **Total** | **37** | **24** | **61%** |

### Priority Breakdown

| Priority | Count | Description |
|----------|-------|-------------|
| Critical | 11 | Block core functionality (protection groups, recovery plans, executions) |
| High | 4 | Limit functionality (server configs, account management) |
| Medium | 6 | Nice to have (tag sync status, capacity conflicts) |
| Low | 3 | Optional features (config history, advanced queries) |


## Frontend Feature to Lambda Operation Mapping

### 1. Protection Groups

| Frontend Feature | API Endpoint | Lambda Handler | Operation | Status | Priority |
|-----------------|--------------|----------------|-----------|--------|----------|
| List protection groups | GET /protection-groups | query-handler | list_protection_groups | ❌ Missing | Critical |
| Get protection group details | GET /protection-groups/{id} | query-handler | get_protection_group | ❌ Missing | Critical |
| Create protection group | POST /protection-groups | data-management-handler | create_protection_group | ✅ Implemented | - |
| Update protection group | PUT /protection-groups/{id} | data-management-handler | update_protection_group | ✅ Implemented | - |
| Delete protection group | DELETE /protection-groups/{id} | data-management-handler | delete_protection_group | ✅ Implemented | - |
| Resolve tag-based servers | POST /protection-groups/resolve-tags | data-management-handler | resolve_protection_group_tags | ✅ Implemented | - |

### 2. Server Launch Configurations

| Frontend Feature | API Endpoint | Lambda Handler | Operation | Status | Priority |
|-----------------|--------------|----------------|-----------|--------|----------|
| Get server launch config | GET /protection-groups/{id}/servers/{serverId}/launch-config | query-handler | get_server_launch_config | ❌ Missing | High |
| Update server launch config | PUT /protection-groups/{id}/servers/{serverId}/launch-config | data-management-handler | update_server_launch_config | ⚠️ API Gateway only | High |
| Delete server launch config | DELETE /protection-groups/{id}/servers/{serverId}/launch-config | data-management-handler | delete_server_launch_config | ⚠️ API Gateway only | High |
| Bulk update server configs | POST /protection-groups/{id}/servers/bulk-launch-config | data-management-handler | bulk_update_server_configs | ⚠️ API Gateway only | High |
| Validate static IP | POST /protection-groups/{id}/servers/{serverId}/validate-ip | data-management-handler | validate_static_ip | ⚠️ API Gateway only | Medium |
| Get config history | GET /protection-groups/{id}/servers/{serverId}/config-history | query-handler | get_server_config_history | ❌ Missing | Low |

### 3. Recovery Plans

| Frontend Feature | API Endpoint | Lambda Handler | Operation | Status | Priority |
|-----------------|--------------|----------------|-----------|--------|----------|
| List recovery plans | GET /recovery-plans | query-handler | list_recovery_plans | ❌ Missing | Critical |
| Get recovery plan details | GET /recovery-plans/{id} | query-handler | get_recovery_plan | ❌ Missing | Critical |
| Create recovery plan | POST /recovery-plans | data-management-handler | create_recovery_plan | ✅ Implemented | - |
| Update recovery plan | PUT /recovery-plans/{id} | data-management-handler | update_recovery_plan | ✅ Implemented | - |
| Delete recovery plan | DELETE /recovery-plans/{id} | data-management-handler | delete_recovery_plan | ✅ Implemented | - |


### 4. Executions

| Frontend Feature | API Endpoint | Lambda Handler | Operation | Status | Priority |
|-----------------|--------------|----------------|-----------|--------|----------|
| List executions | GET /executions | query-handler | list_executions | ❌ Missing | Critical |
| Get execution details | GET /executions/{id} | query-handler | get_execution | ❌ Missing | Critical |
| Start execution | POST /executions | execution-handler | start_execution | ✅ Implemented | - |
| Cancel execution | POST /executions/{id}/cancel | execution-handler | cancel_execution | ❌ Missing | Critical |
| Pause execution | POST /executions/{id}/pause | execution-handler | pause_execution | ❌ Missing | Critical |
| Resume execution | POST /executions/{id}/resume | execution-handler | resume_execution | ❌ Missing | Critical |
| Terminate instances | POST /executions/{id}/terminate-instances | execution-handler | terminate_instances | ❌ Missing | Critical |
| Get recovery instances | GET /executions/{id}/recovery-instances | execution-handler | get_recovery_instances | ❌ Missing | Medium |
| Get job logs | GET /executions/{id}/job-logs | execution-handler | get_job_logs | ❌ Missing | Medium |
| Get termination status | GET /executions/{id}/termination-status | execution-handler | get_termination_status | ❌ Missing | Medium |
| Delete executions | DELETE /executions | execution-handler | delete_executions | ❌ Missing | Low |

### 5. DRS Infrastructure

| Frontend Feature | API Endpoint | Lambda Handler | Operation | Status | Priority |
|-----------------|--------------|----------------|-----------|--------|----------|
| List DRS source servers | GET /drs/source-servers | query-handler | get_drs_source_servers | ✅ Implemented | - |
| Get DRS account capacity | GET /drs/capacity | query-handler | get_drs_account_capacity | ✅ Implemented | - |
| Get all regions capacity | GET /drs/capacity/all-regions | query-handler | get_drs_account_capacity_all_regions | ✅ Implemented | - |
| Get regional capacity | GET /drs/capacity/regional | query-handler | get_drs_regional_capacity | ✅ Implemented | - |
| Get capacity conflicts | GET /drs/capacity/conflicts | query-handler | get_drs_capacity_conflicts | ❌ Missing | Medium |

### 6. Account Management

| Frontend Feature | API Endpoint | Lambda Handler | Operation | Status | Priority |
|-----------------|--------------|----------------|-----------|--------|----------|
| List target accounts | GET /accounts/targets | query-handler | get_target_accounts | ✅ Implemented | - |
| Add target account | POST /accounts/targets | data-management-handler | add_target_account | ⚠️ API Gateway only | High |
| Update target account | PUT /accounts/targets/{id} | data-management-handler | update_target_account | ⚠️ API Gateway only | High |
| Delete target account | DELETE /accounts/targets/{id} | data-management-handler | delete_target_account | ⚠️ API Gateway only | High |
| Get current account ID | GET /accounts/current | query-handler | get_current_account_id | ✅ Implemented | - |


### 7. Staging Accounts

| Frontend Feature | API Endpoint | Lambda Handler | Operation | Status | Priority |
|-----------------|--------------|----------------|-----------|--------|----------|
| Discover staging accounts | GET /accounts/staging/discover | query-handler | discover_staging_accounts | ✅ Implemented | - |
| Get combined capacity | GET /accounts/staging/capacity | query-handler | get_combined_capacity | ✅ Implemented | - |
| Validate staging account | POST /accounts/staging/validate | query-handler | validate_staging_account | ✅ Implemented | - |
| Add staging account | POST /accounts/staging | data-management-handler | add_staging_account | ✅ Implemented | - |
| Remove staging account | DELETE /accounts/staging | data-management-handler | remove_staging_account | ✅ Implemented | - |
| Sync staging accounts | POST /accounts/staging/sync | data-management-handler | sync_staging_accounts | ✅ Implemented | - |

### 8. EC2 Resources

| Frontend Feature | API Endpoint | Lambda Handler | Operation | Status | Priority |
|-----------------|--------------|----------------|-----------|--------|----------|
| List EC2 subnets | GET /ec2/subnets | query-handler | get_ec2_subnets | ✅ Implemented | - |
| List EC2 security groups | GET /ec2/security-groups | query-handler | get_ec2_security_groups | ✅ Implemented | - |
| List EC2 instance profiles | GET /ec2/instance-profiles | query-handler | get_ec2_instance_profiles | ✅ Implemented | - |
| List EC2 instance types | GET /ec2/instance-types | query-handler | get_ec2_instance_types | ✅ Implemented | - |

### 9. Tag Synchronization

| Frontend Feature | API Endpoint | Lambda Handler | Operation | Status | Priority |
|-----------------|--------------|----------------|-----------|--------|----------|
| Get tag sync status | GET /tag-sync/status | query-handler | get_tag_sync_status | ❌ Missing | Medium |
| Get tag sync settings | GET /tag-sync/settings | data-management-handler | get_tag_sync_settings | ✅ Implemented | - |
| Update tag sync settings | PUT /tag-sync/settings | data-management-handler | update_tag_sync_settings | ✅ Implemented | - |
| Trigger tag sync | POST /tag-sync/trigger | data-management-handler | handle_drs_tag_sync | ✅ Implemented | - |

### 10. Configuration Management

| Frontend Feature | API Endpoint | Lambda Handler | Operation | Status | Priority |
|-----------------|--------------|----------------|-----------|--------|----------|
| Export configuration | GET /config/export | query-handler | export_configuration | ✅ Implemented | - |
| Import configuration | POST /config/import | data-management-handler | import_configuration | ✅ Implemented | - |

### 11. User Permissions

| Frontend Feature | API Endpoint | Lambda Handler | Operation | Status | Priority |
|-----------------|--------------|----------------|-----------|--------|----------|
| Get user permissions | GET /user/permissions | query-handler | get_user_permissions | ⚠️ Not supported in direct mode | Low |


## Operation Coverage Matrix

### Query Handler Operations

| Operation | Required By | Status | Priority | Implementation Effort | Notes |
|-----------|-------------|--------|----------|----------------------|-------|
| list_protection_groups | Frontend listing | ❌ Missing | Critical | Medium | Needs DynamoDB query + enrichment |
| get_protection_group | Frontend detail view | ❌ Missing | Critical | Medium | Needs DynamoDB get + server details |
| get_server_launch_config | Server config view | ❌ Missing | High | Low | Simple DynamoDB query |
| get_server_config_history | Config audit trail | ❌ Missing | Low | Medium | Needs audit log query |
| list_recovery_plans | Frontend listing | ❌ Missing | Critical | Medium | Needs DynamoDB query + enrichment |
| get_recovery_plan | Frontend detail view | ❌ Missing | Critical | Medium | Needs DynamoDB get + wave details |
| list_executions | Frontend listing | ❌ Missing | Critical | Medium | Needs DynamoDB query + filtering |
| get_execution | Frontend detail view | ❌ Missing | Critical | Low | Delegate to execution-handler |
| get_tag_sync_status | Tag sync monitoring | ❌ Missing | Medium | Low | Simple status query |
| get_drs_capacity_conflicts | Capacity planning | ❌ Missing | Medium | High | Complex cross-account analysis |
| get_drs_source_servers | DRS infrastructure | ✅ Implemented | - | - | Already working |
| get_drs_account_capacity | Capacity queries | ✅ Implemented | - | - | Already working |
| get_drs_account_capacity_all_regions | Multi-region capacity | ✅ Implemented | - | - | Already working |
| get_drs_regional_capacity | Regional capacity | ✅ Implemented | - | - | Already working |
| get_target_accounts | Account management | ✅ Implemented | - | - | Already working |
| discover_staging_accounts | Staging account discovery | ✅ Implemented | - | - | Already working |
| get_combined_capacity | Combined capacity | ✅ Implemented | - | - | Already working |
| validate_staging_account | Staging validation | ✅ Implemented | - | - | Already working |
| get_ec2_subnets | EC2 resource queries | ✅ Implemented | - | - | Already working |
| get_ec2_security_groups | EC2 resource queries | ✅ Implemented | - | - | Already working |
| get_ec2_instance_profiles | EC2 resource queries | ✅ Implemented | - | - | Already working |
| get_ec2_instance_types | EC2 resource queries | ✅ Implemented | - | - | Already working |
| get_current_account_id | Account info | ✅ Implemented | - | - | Already working |
| export_configuration | Config export | ✅ Implemented | - | - | Already working |
| sync_staging_accounts | Staging sync | ✅ Implemented | - | - | Already working |

**Summary**: 16 implemented, 11 missing (59% coverage)


### Data Management Handler Operations

| Operation | Required By | Status | Priority | Implementation Effort | Notes |
|-----------|-------------|--------|----------|----------------------|-------|
| update_server_launch_config | Server config management | ⚠️ API Gateway only | High | Low | Function exists, just add to direct invocation |
| delete_server_launch_config | Server config management | ⚠️ API Gateway only | High | Low | Function exists, just add to direct invocation |
| bulk_update_server_configs | Bulk operations | ⚠️ API Gateway only | High | Low | Function exists, just add to direct invocation |
| validate_static_ip | IP validation | ⚠️ API Gateway only | Medium | Low | Function exists, just add to direct invocation |
| add_target_account | Account management | ⚠️ API Gateway only | High | Low | Function exists, just add to direct invocation |
| update_target_account | Account management | ⚠️ API Gateway only | High | Low | Function exists, just add to direct invocation |
| delete_target_account | Account management | ⚠️ API Gateway only | High | Low | Function exists, just add to direct invocation |
| create_protection_group | Protection group CRUD | ✅ Implemented | - | - | Already working |
| update_protection_group | Protection group CRUD | ✅ Implemented | - | - | Already working |
| delete_protection_group | Protection group CRUD | ✅ Implemented | - | - | Already working |
| resolve_protection_group_tags | Tag-based selection | ✅ Implemented | - | - | Already working |
| list_protection_groups | Frontend listing | ✅ Implemented | - | - | Already working |
| get_protection_group | Frontend detail view | ✅ Implemented | - | - | Already working |
| create_recovery_plan | Recovery plan CRUD | ✅ Implemented | - | - | Already working |
| update_recovery_plan | Recovery plan CRUD | ✅ Implemented | - | - | Already working |
| delete_recovery_plan | Recovery plan CRUD | ✅ Implemented | - | - | Already working |
| list_recovery_plans | Frontend listing | ✅ Implemented | - | - | Already working |
| get_recovery_plan | Frontend detail view | ✅ Implemented | - | - | Already working |
| add_staging_account | Staging account management | ✅ Implemented | - | - | Already working |
| remove_staging_account | Staging account management | ✅ Implemented | - | - | Already working |
| sync_staging_accounts | Staging sync | ✅ Implemented | - | - | Already working |
| handle_drs_tag_sync | Tag synchronization | ✅ Implemented | - | - | Already working |
| get_tag_sync_settings | Tag sync config | ✅ Implemented | - | - | Already working |
| update_tag_sync_settings | Tag sync config | ✅ Implemented | - | - | Already working |
| import_configuration | Config import | ✅ Implemented | - | - | Already working |

**Summary**: 18 implemented, 7 missing (72% coverage)

**Note**: The 7 "missing" operations are actually implemented but only exposed via API Gateway. They need to be added to the `handle_direct_invocation()` operations dictionary.


### Execution Handler Operations

| Operation | Required By | Status | Priority | Implementation Effort | Notes |
|-----------|-------------|--------|----------|----------------------|-------|
| cancel_execution | Execution control | ❌ Missing | Critical | Low | Function exists, needs standardization |
| pause_execution | Execution control | ❌ Missing | Critical | Low | Function exists, needs standardization |
| resume_execution | Execution control | ❌ Missing | Critical | Low | Function exists, needs standardization |
| terminate_instances | Instance cleanup | ❌ Missing | Critical | Low | Function exists, needs standardization |
| get_recovery_instances | Instance monitoring | ❌ Missing | Medium | Low | Function exists, needs standardization |
| get_job_logs | Troubleshooting | ❌ Missing | Medium | Low | Function exists, needs standardization |
| get_termination_status | Cleanup monitoring | ❌ Missing | Medium | Low | Function exists, needs standardization |
| delete_executions | Cleanup | ❌ Missing | Low | Low | Function exists, needs standardization |
| start_execution | Execution initiation | ✅ Implemented | - | - | Already working via operation pattern |
| get_execution_details | Execution monitoring | ✅ Implemented | - | - | Already working via operation pattern |
| list_executions | Frontend listing | ⚠️ Should delegate | Critical | Low | Should delegate to query-handler |

**Summary**: 3 implemented (including partial), 8 missing (27% coverage)

**Note**: Execution-handler has partial direct invocation support through operation-based pattern but lacks standardized `handle_direct_invocation()` function. Most operations exist but need to be exposed through standardized interface.


## Gap Analysis

### Critical Gaps (Block Core Functionality)

These operations are **essential** for basic application functionality and must be implemented in Phase 3:

#### Query Handler - Protection Groups (2 operations)
1. **list_protection_groups**
   - **Impact**: Frontend cannot display protection groups list
   - **Workaround**: None - blocks entire protection groups feature
   - **Implementation**: Medium effort - DynamoDB query + server enrichment
   - **Priority**: P0 - Must have for MVP

2. **get_protection_group**
   - **Impact**: Frontend cannot display protection group details
   - **Workaround**: None - blocks detail view and editing
   - **Implementation**: Medium effort - DynamoDB get + server details
   - **Priority**: P0 - Must have for MVP

#### Query Handler - Recovery Plans (2 operations)
3. **list_recovery_plans**
   - **Impact**: Frontend cannot display recovery plans list
   - **Workaround**: None - blocks entire recovery plans feature
   - **Implementation**: Medium effort - DynamoDB query + wave enrichment
   - **Priority**: P0 - Must have for MVP

4. **get_recovery_plan**
   - **Impact**: Frontend cannot display recovery plan details
   - **Workaround**: None - blocks detail view and editing
   - **Implementation**: Medium effort - DynamoDB get + wave details
   - **Priority**: P0 - Must have for MVP

#### Query Handler - Executions (2 operations)
5. **list_executions**
   - **Impact**: Frontend cannot display executions list
   - **Workaround**: None - blocks execution monitoring
   - **Implementation**: Medium effort - DynamoDB query + filtering
   - **Priority**: P0 - Must have for MVP

6. **get_execution**
   - **Impact**: Frontend cannot display execution details
   - **Workaround**: Delegate to execution-handler's get_execution_details
   - **Implementation**: Low effort - simple delegation
   - **Priority**: P0 - Must have for MVP

#### Execution Handler - Lifecycle Control (5 operations)
7. **cancel_execution**
   - **Impact**: Cannot stop running executions
   - **Workaround**: None - critical safety feature
   - **Implementation**: Low effort - function exists, needs standardization
   - **Priority**: P0 - Must have for safety

8. **pause_execution**
   - **Impact**: Cannot pause executions at wave boundaries
   - **Workaround**: None - important control feature
   - **Implementation**: Low effort - function exists, needs standardization
   - **Priority**: P0 - Must have for control

9. **resume_execution**
   - **Impact**: Cannot resume paused executions
   - **Workaround**: None - required for pause feature
   - **Implementation**: Low effort - function exists, needs standardization
   - **Priority**: P0 - Must have for control

10. **terminate_instances**
    - **Impact**: Cannot cleanup recovery instances
    - **Workaround**: Manual AWS console cleanup
    - **Implementation**: Low effort - function exists, needs standardization
    - **Priority**: P0 - Must have for cleanup

11. **get_recovery_instances**
    - **Impact**: Cannot monitor recovery instance status
    - **Workaround**: Check AWS console
    - **Implementation**: Low effort - function exists, needs standardization
    - **Priority**: P1 - Important for monitoring

**Critical Gap Summary**: 11 operations blocking core functionality


### High Priority Gaps (Limit Functionality)

These operations are **important** for full feature support but have workarounds:

#### Data Management Handler - Server Configurations (4 operations)
1. **update_server_launch_config**
   - **Impact**: Cannot update individual server launch configurations
   - **Workaround**: Update entire protection group
   - **Implementation**: Low effort - function exists, just add to direct invocation
   - **Priority**: P1 - Important for granular control

2. **delete_server_launch_config**
   - **Impact**: Cannot reset server to group defaults
   - **Workaround**: Update with empty config
   - **Implementation**: Low effort - function exists, just add to direct invocation
   - **Priority**: P1 - Important for config management

3. **bulk_update_server_configs**
   - **Impact**: Cannot efficiently update multiple servers
   - **Workaround**: Update servers one at a time
   - **Implementation**: Low effort - function exists, just add to direct invocation
   - **Priority**: P1 - Important for efficiency

#### Data Management Handler - Account Management (3 operations)
4. **add_target_account**
   - **Impact**: Cannot add new target accounts
   - **Workaround**: Manual DynamoDB entry (not recommended)
   - **Implementation**: Low effort - function exists, just add to direct invocation
   - **Priority**: P1 - Important for multi-account setup

5. **update_target_account**
   - **Impact**: Cannot update target account configuration
   - **Workaround**: Delete and recreate account
   - **Implementation**: Low effort - function exists, just add to direct invocation
   - **Priority**: P1 - Important for account management

6. **delete_target_account**
   - **Impact**: Cannot remove target accounts
   - **Workaround**: Manual DynamoDB deletion (not recommended)
   - **Implementation**: Low effort - function exists, just add to direct invocation
   - **Priority**: P1 - Important for account cleanup

#### Query Handler - Server Configuration (1 operation)
7. **get_server_launch_config**
   - **Impact**: Cannot view individual server launch configuration
   - **Workaround**: Get entire protection group and extract server config
   - **Implementation**: Low effort - simple DynamoDB query
   - **Priority**: P1 - Important for detail view

**High Priority Gap Summary**: 7 operations limiting functionality


### Medium Priority Gaps (Nice to Have)

These operations enhance the user experience but are not essential:

#### Execution Handler - Monitoring (3 operations)
1. **get_job_logs**
   - **Impact**: Cannot view DRS job logs from frontend
   - **Workaround**: Check AWS DRS console
   - **Implementation**: Low effort - function exists, needs standardization
   - **Priority**: P2 - Nice to have for troubleshooting

2. **get_termination_status**
   - **Impact**: Cannot monitor instance termination progress
   - **Workaround**: Check execution status
   - **Implementation**: Low effort - function exists, needs standardization
   - **Priority**: P2 - Nice to have for monitoring

#### Query Handler - Tag Sync (1 operation)
3. **get_tag_sync_status**
   - **Impact**: Cannot view tag synchronization status
   - **Workaround**: Check CloudWatch logs
   - **Implementation**: Low effort - simple status query
   - **Priority**: P2 - Nice to have for monitoring

#### Query Handler - Capacity Planning (1 operation)
4. **get_drs_capacity_conflicts**
   - **Impact**: Cannot detect capacity conflicts across accounts
   - **Workaround**: Manual capacity calculation
   - **Implementation**: High effort - complex cross-account analysis
   - **Priority**: P2 - Nice to have for planning

#### Data Management Handler - IP Validation (1 operation)
5. **validate_static_ip**
   - **Impact**: Cannot validate static IP before assignment
   - **Workaround**: Try assignment and handle errors
   - **Implementation**: Low effort - function exists, just add to direct invocation
   - **Priority**: P2 - Nice to have for validation

**Medium Priority Gap Summary**: 5 operations enhancing user experience

### Low Priority Gaps (Optional Features)

These operations are optional enhancements:

#### Query Handler - Audit Trail (1 operation)
1. **get_server_config_history**
   - **Impact**: Cannot view configuration change history
   - **Workaround**: None - feature not critical
   - **Implementation**: Medium effort - audit log query
   - **Priority**: P3 - Optional for audit compliance

#### Execution Handler - Cleanup (1 operation)
2. **delete_executions**
   - **Impact**: Cannot bulk delete old executions
   - **Workaround**: Manual DynamoDB cleanup
   - **Implementation**: Low effort - function exists, needs standardization
   - **Priority**: P3 - Optional for housekeeping

**Low Priority Gap Summary**: 2 operations for optional features


## Implementation Roadmap

### Phase 3.1: Critical Operations (Week 1-2)

**Goal**: Enable core frontend functionality

#### Query Handler - Protection Groups & Recovery Plans (4 operations)
- [ ] `list_protection_groups` - DynamoDB query + server enrichment
- [ ] `get_protection_group` - DynamoDB get + server details
- [ ] `list_recovery_plans` - DynamoDB query + wave enrichment
- [ ] `get_recovery_plan` - DynamoDB get + wave details

**Estimated Effort**: 3-4 days
**Dependencies**: None
**Testing**: Unit tests + property-based tests for each operation

#### Query Handler - Executions (2 operations)
- [ ] `list_executions` - DynamoDB query + filtering
- [ ] `get_execution` - Delegate to execution-handler

**Estimated Effort**: 1-2 days
**Dependencies**: None
**Testing**: Unit tests + integration tests with execution-handler

#### Execution Handler - Lifecycle Control (5 operations)
- [ ] Create `handle_direct_invocation()` function
- [ ] `cancel_execution` - Standardize existing function
- [ ] `pause_execution` - Standardize existing function
- [ ] `resume_execution` - Standardize existing function
- [ ] `terminate_instances` - Standardize existing function
- [ ] `get_recovery_instances` - Standardize existing function

**Estimated Effort**: 2-3 days
**Dependencies**: None
**Testing**: Unit tests + integration tests with Step Functions

**Phase 3.1 Total**: 6-9 days (11 operations)

### Phase 3.2: High Priority Operations (Week 3)

**Goal**: Enable full feature support

#### Data Management Handler - Server Configurations (4 operations)
- [ ] `update_server_launch_config` - Add to direct invocation
- [ ] `delete_server_launch_config` - Add to direct invocation
- [ ] `bulk_update_server_configs` - Add to direct invocation
- [ ] `validate_static_ip` - Add to direct invocation

**Estimated Effort**: 1 day (functions already exist)
**Dependencies**: None
**Testing**: Unit tests for direct invocation routing

#### Data Management Handler - Account Management (3 operations)
- [ ] `add_target_account` - Add to direct invocation
- [ ] `update_target_account` - Add to direct invocation
- [ ] `delete_target_account` - Add to direct invocation

**Estimated Effort**: 1 day (functions already exist)
**Dependencies**: None
**Testing**: Unit tests for direct invocation routing

#### Query Handler - Server Configuration (1 operation)
- [ ] `get_server_launch_config` - Simple DynamoDB query

**Estimated Effort**: 0.5 days
**Dependencies**: None
**Testing**: Unit tests + property-based tests

**Phase 3.2 Total**: 2-3 days (8 operations)


### Phase 3.3: Medium Priority Operations (Week 4)

**Goal**: Enhance monitoring and validation

#### Execution Handler - Monitoring (3 operations)
- [ ] `get_job_logs` - Standardize existing function
- [ ] `get_termination_status` - Standardize existing function
- [ ] `delete_executions` - Standardize existing function

**Estimated Effort**: 1 day
**Dependencies**: Phase 3.1 (execution-handler standardization)
**Testing**: Unit tests for direct invocation routing

#### Query Handler - Tag Sync & Capacity (2 operations)
- [ ] `get_tag_sync_status` - Simple status query
- [ ] `get_drs_capacity_conflicts` - Complex cross-account analysis

**Estimated Effort**: 2-3 days (capacity conflicts is complex)
**Dependencies**: None
**Testing**: Unit tests + integration tests for capacity conflicts

**Phase 3.3 Total**: 3-4 days (5 operations)

### Phase 3.4: Low Priority Operations (Week 5)

**Goal**: Complete optional features

#### Query Handler - Audit Trail (1 operation)
- [ ] `get_server_config_history` - Audit log query

**Estimated Effort**: 1-2 days
**Dependencies**: None
**Testing**: Unit tests + property-based tests

**Phase 3.4 Total**: 1-2 days (1 operation)

### Total Implementation Timeline

| Phase | Duration | Operations | Priority |
|-------|----------|------------|----------|
| Phase 3.1 | 6-9 days | 11 | Critical |
| Phase 3.2 | 2-3 days | 8 | High |
| Phase 3.3 | 3-4 days | 5 | Medium |
| Phase 3.4 | 1-2 days | 1 | Low |
| **Total** | **12-18 days** | **25** | **All** |

### Parallel Work Opportunities

The following phases can be worked on in parallel:

1. **Query Handler** (Phases 3.1, 3.2, 3.4) - Independent work stream
2. **Data Management Handler** (Phase 3.2) - Independent work stream
3. **Execution Handler** (Phases 3.1, 3.3) - Independent work stream

With 2-3 developers working in parallel, total timeline can be reduced to **8-12 days**.


## Cross-Reference Table

### Frontend → API Gateway → Lambda Operation Mapping

| Frontend Component | User Action | API Endpoint | Lambda Handler | Operation | Status |
|-------------------|-------------|--------------|----------------|-----------|--------|
| **Protection Groups List** | View list | GET /protection-groups | query-handler | list_protection_groups | ❌ Missing |
| **Protection Groups List** | Create new | POST /protection-groups | data-management-handler | create_protection_group | ✅ Implemented |
| **Protection Group Detail** | View details | GET /protection-groups/{id} | query-handler | get_protection_group | ❌ Missing |
| **Protection Group Detail** | Update group | PUT /protection-groups/{id} | data-management-handler | update_protection_group | ✅ Implemented |
| **Protection Group Detail** | Delete group | DELETE /protection-groups/{id} | data-management-handler | delete_protection_group | ✅ Implemented |
| **Protection Group Detail** | Preview tag selection | POST /protection-groups/resolve-tags | data-management-handler | resolve_protection_group_tags | ✅ Implemented |
| **Server Launch Config** | View config | GET /protection-groups/{id}/servers/{serverId}/launch-config | query-handler | get_server_launch_config | ❌ Missing |
| **Server Launch Config** | Update config | PUT /protection-groups/{id}/servers/{serverId}/launch-config | data-management-handler | update_server_launch_config | ⚠️ API Gateway only |
| **Server Launch Config** | Delete config | DELETE /protection-groups/{id}/servers/{serverId}/launch-config | data-management-handler | delete_server_launch_config | ⚠️ API Gateway only |
| **Server Launch Config** | Bulk update | POST /protection-groups/{id}/servers/bulk-launch-config | data-management-handler | bulk_update_server_configs | ⚠️ API Gateway only |
| **Server Launch Config** | Validate IP | POST /protection-groups/{id}/servers/{serverId}/validate-ip | data-management-handler | validate_static_ip | ⚠️ API Gateway only |
| **Recovery Plans List** | View list | GET /recovery-plans | query-handler | list_recovery_plans | ❌ Missing |
| **Recovery Plans List** | Create new | POST /recovery-plans | data-management-handler | create_recovery_plan | ✅ Implemented |
| **Recovery Plan Detail** | View details | GET /recovery-plans/{id} | query-handler | get_recovery_plan | ❌ Missing |
| **Recovery Plan Detail** | Update plan | PUT /recovery-plans/{id} | data-management-handler | update_recovery_plan | ✅ Implemented |
| **Recovery Plan Detail** | Delete plan | DELETE /recovery-plans/{id} | data-management-handler | delete_recovery_plan | ✅ Implemented |
| **Recovery Plan Detail** | Start execution | POST /executions | execution-handler | start_execution | ✅ Implemented |
| **Executions List** | View list | GET /executions | query-handler | list_executions | ❌ Missing |
| **Execution Detail** | View details | GET /executions/{id} | query-handler | get_execution | ❌ Missing |
| **Execution Detail** | Cancel execution | POST /executions/{id}/cancel | execution-handler | cancel_execution | ❌ Missing |
| **Execution Detail** | Pause execution | POST /executions/{id}/pause | execution-handler | pause_execution | ❌ Missing |
| **Execution Detail** | Resume execution | POST /executions/{id}/resume | execution-handler | resume_execution | ❌ Missing |
| **Execution Detail** | Terminate instances | POST /executions/{id}/terminate-instances | execution-handler | terminate_instances | ❌ Missing |
| **Execution Detail** | View recovery instances | GET /executions/{id}/recovery-instances | execution-handler | get_recovery_instances | ❌ Missing |
| **Execution Detail** | View job logs | GET /executions/{id}/job-logs | execution-handler | get_job_logs | ❌ Missing |
| **DRS Infrastructure** | List source servers | GET /drs/source-servers | query-handler | get_drs_source_servers | ✅ Implemented |
| **DRS Infrastructure** | Get capacity | GET /drs/capacity | query-handler | get_drs_account_capacity | ✅ Implemented |
| **DRS Infrastructure** | Get all regions capacity | GET /drs/capacity/all-regions | query-handler | get_drs_account_capacity_all_regions | ✅ Implemented |
| **DRS Infrastructure** | Get capacity conflicts | GET /drs/capacity/conflicts | query-handler | get_drs_capacity_conflicts | ❌ Missing |
| **Account Management** | List target accounts | GET /accounts/targets | query-handler | get_target_accounts | ✅ Implemented |
| **Account Management** | Add target account | POST /accounts/targets | data-management-handler | add_target_account | ⚠️ API Gateway only |
| **Account Management** | Update target account | PUT /accounts/targets/{id} | data-management-handler | update_target_account | ⚠️ API Gateway only |
| **Account Management** | Delete target account | DELETE /accounts/targets/{id} | data-management-handler | delete_target_account | ⚠️ API Gateway only |
| **Staging Accounts** | Discover accounts | GET /accounts/staging/discover | query-handler | discover_staging_accounts | ✅ Implemented |
| **Staging Accounts** | Get combined capacity | GET /accounts/staging/capacity | query-handler | get_combined_capacity | ✅ Implemented |
| **Staging Accounts** | Validate account | POST /accounts/staging/validate | query-handler | validate_staging_account | ✅ Implemented |
| **Staging Accounts** | Add account | POST /accounts/staging | data-management-handler | add_staging_account | ✅ Implemented |
| **Staging Accounts** | Remove account | DELETE /accounts/staging | data-management-handler | remove_staging_account | ✅ Implemented |
| **Staging Accounts** | Sync accounts | POST /accounts/staging/sync | data-management-handler | sync_staging_accounts | ✅ Implemented |
| **Tag Sync** | Get status | GET /tag-sync/status | query-handler | get_tag_sync_status | ❌ Missing |
| **Tag Sync** | Get settings | GET /tag-sync/settings | data-management-handler | get_tag_sync_settings | ✅ Implemented |
| **Tag Sync** | Update settings | PUT /tag-sync/settings | data-management-handler | update_tag_sync_settings | ✅ Implemented |
| **Tag Sync** | Trigger sync | POST /tag-sync/trigger | data-management-handler | handle_drs_tag_sync | ✅ Implemented |
| **Configuration** | Export config | GET /config/export | query-handler | export_configuration | ✅ Implemented |
| **Configuration** | Import config | POST /config/import | data-management-handler | import_configuration | ✅ Implemented |


## Testing Strategy

### Unit Testing Requirements

Each operation must have:

1. **Happy Path Tests**
   - Valid input → Expected output
   - Verify correct handler function called
   - Verify correct parameters passed

2. **Error Handling Tests**
   - Missing required parameters
   - Invalid parameter values
   - DynamoDB errors
   - AWS API errors

3. **Edge Case Tests**
   - Empty results
   - Large result sets (pagination)
   - Concurrent operations
   - Resource not found

### Property-Based Testing Requirements

Critical operations should have property-based tests:

1. **list_protection_groups**
   - Property: Result count ≤ total items in database
   - Property: All returned items have required fields
   - Property: Pagination tokens are valid

2. **list_recovery_plans**
   - Property: Result count ≤ total items in database
   - Property: All returned items have required fields
   - Property: Wave counts are accurate

3. **list_executions**
   - Property: Result count ≤ total items in database
   - Property: Filtering reduces result count
   - Property: Status values are valid enum values

### Integration Testing Requirements

End-to-end tests for critical workflows:

1. **Protection Group Lifecycle**
   - Create → List (verify appears) → Get (verify details) → Update → Get (verify changes) → Delete → List (verify removed)

2. **Recovery Plan Lifecycle**
   - Create → List (verify appears) → Get (verify details) → Update → Get (verify changes) → Delete → List (verify removed)

3. **Execution Lifecycle**
   - Start → List (verify appears) → Get (verify status) → Pause → Get (verify paused) → Resume → Get (verify resumed) → Cancel → Get (verify cancelled)

### Performance Testing Requirements

Load tests for high-volume operations:

1. **list_protection_groups** - 1000+ groups
2. **list_recovery_plans** - 500+ plans
3. **list_executions** - 10,000+ executions
4. **get_drs_source_servers** - 1000+ servers

Target: < 3 seconds for list operations with pagination


## Risk Assessment

### High Risk Operations

Operations that could cause data loss or service disruption:

1. **delete_protection_group**
   - **Risk**: Accidental deletion of production protection groups
   - **Mitigation**: Require confirmation, check for active executions, soft delete with recovery period

2. **delete_recovery_plan**
   - **Risk**: Accidental deletion of production recovery plans
   - **Mitigation**: Require confirmation, check for active executions, soft delete with recovery period

3. **cancel_execution**
   - **Risk**: Cancelling production recovery execution
   - **Mitigation**: Require confirmation, log cancellation reason, preserve execution state

4. **terminate_instances**
   - **Risk**: Terminating production recovery instances
   - **Mitigation**: Require confirmation, verify execution is not in critical state

5. **delete_target_account**
   - **Risk**: Removing account with active protection groups
   - **Mitigation**: Check for dependent resources, require force flag

### Medium Risk Operations

Operations that could cause configuration issues:

1. **update_protection_group**
   - **Risk**: Breaking server selection or launch configurations
   - **Mitigation**: Validate all changes, preserve previous version

2. **update_recovery_plan**
   - **Risk**: Creating invalid wave dependencies
   - **Mitigation**: Validate wave graph, check for circular dependencies

3. **bulk_update_server_configs**
   - **Risk**: Applying incorrect configs to multiple servers
   - **Mitigation**: Dry-run mode, validate all configs before applying

### Low Risk Operations

Read-only operations with minimal risk:

- All `list_*` operations
- All `get_*` operations
- `export_configuration`
- `get_tag_sync_status`

## Security Considerations

### Authentication & Authorization

1. **Direct Invocation Mode**
   - No Cognito authentication available
   - Must rely on IAM permissions for Lambda invocation
   - Frontend must handle authentication separately

2. **RBAC Enforcement**
   - `get_user_permissions` not available in direct mode
   - Must implement alternative RBAC mechanism
   - Consider passing user context in event payload

3. **Cross-Account Access**
   - Operations supporting `accountId` parameter must validate access
   - Use IAM assume role for cross-account operations
   - Log all cross-account operations for audit

### Input Validation

All operations must validate:

1. **Required Parameters**
   - Return 400 error if missing
   - List required parameters in error message

2. **Parameter Types**
   - Validate data types (string, number, boolean)
   - Validate format (UUID, email, ARN)

3. **Parameter Values**
   - Validate enum values (status, priority, etc.)
   - Validate ranges (page size, limits)
   - Sanitize string inputs

### Audit Logging

All write operations must log:

1. **Operation Details**
   - Operation name
   - Timestamp
   - User/caller identity
   - Parameters

2. **Result**
   - Success/failure
   - Error message if failed
   - Resource IDs affected

3. **Context**
   - Execution ID (if applicable)
   - Account ID
   - Region


## Recommendations

### Immediate Actions (Phase 3.1)

1. **Prioritize Critical Operations**
   - Focus on 11 critical operations first
   - These enable core frontend functionality
   - Target: Complete in 6-9 days

2. **Standardize Execution Handler**
   - Create `handle_direct_invocation()` function
   - Match pattern used in query-handler and data-management-handler
   - Maintain backward compatibility with existing patterns

3. **Implement Query Operations**
   - `list_protection_groups`, `get_protection_group`
   - `list_recovery_plans`, `get_recovery_plan`
   - `list_executions`, `get_execution`
   - These are most complex and should be started first

### Short-Term Actions (Phase 3.2)

1. **Add Missing Data Management Operations**
   - 7 operations already implemented for API Gateway
   - Just need to add to `handle_direct_invocation()` dictionary
   - Low effort, high value
   - Target: Complete in 2-3 days

2. **Improve Error Handling**
   - Use `response()` utility for consistent error format
   - Add parameter validation before calling operations
   - Return helpful error messages with required parameters

### Medium-Term Actions (Phase 3.3-3.4)

1. **Complete Monitoring Operations**
   - `get_job_logs`, `get_termination_status`
   - `get_tag_sync_status`
   - Enhance troubleshooting capabilities

2. **Implement Capacity Conflict Detection**
   - Complex cross-account analysis
   - Important for capacity planning
   - Can be deferred if time-constrained

### Long-Term Improvements

1. **Operation Discovery**
   - Add `list_operations` operation to each handler
   - Return categorized list of supported operations
   - Helps with API documentation and testing

2. **Batch Operations**
   - Consider adding batch versions of common operations
   - Example: `batch_get_protection_groups`
   - Reduces Lambda invocations for bulk queries

3. **Caching Strategy**
   - Implement caching for frequently accessed data
   - Example: DRS source servers, EC2 resources
   - Reduces AWS API calls and improves performance

4. **Async Operations**
   - Consider async pattern for long-running operations
   - Example: `bulk_update_server_configs`
   - Return operation ID, poll for completion

## Success Metrics

### Coverage Metrics

- **Target**: 100% operation coverage (52/52 operations)
- **Current**: 71% operation coverage (37/52 operations)
- **Phase 3.1 Goal**: 92% coverage (48/52 operations)
- **Phase 3.2 Goal**: 100% coverage (52/52 operations)

### Performance Metrics

- **List Operations**: < 3 seconds (with pagination)
- **Get Operations**: < 1 second
- **Write Operations**: < 2 seconds
- **Bulk Operations**: < 5 seconds

### Quality Metrics

- **Unit Test Coverage**: > 90%
- **Property-Based Tests**: All list/query operations
- **Integration Tests**: All critical workflows
- **Error Handling**: 100% of operations

### User Experience Metrics

- **Frontend Feature Parity**: 100% (all features work in direct mode)
- **Error Messages**: Clear and actionable
- **Response Times**: Comparable to API Gateway mode

## Conclusion

The operation inventory reveals that **71% of required operations are implemented**, with **29% missing**. The gaps are concentrated in three areas:

1. **Query Handler** (59% coverage) - Missing 11 operations for listing and retrieving resources
2. **Data Management Handler** (72% coverage) - Missing 7 operations (already implemented, just need exposure)
3. **Execution Handler** (33% coverage) - Missing 8 operations (need standardization)

The **critical path** is implementing the 11 missing query operations and standardizing the execution handler. With focused effort, all critical operations can be completed in **6-9 days**, and full coverage achieved in **12-18 days**.

The **highest ROI** activities are:
1. Adding 7 data-management operations to direct invocation (1 day, 7 operations)
2. Standardizing execution handler (2-3 days, 5 operations)
3. Implementing query operations (3-4 days, 6 operations)

This analysis provides a clear roadmap for completing Phase 3 of the direct Lambda invocation mode implementation.

