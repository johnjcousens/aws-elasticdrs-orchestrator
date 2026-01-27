# Shared Functions Analysis - Lambda Handler Deduplication

**Date**: 2026-01-25
**Purpose**: Identify duplicate functions across handlers that should be moved to shared modules

## Executive Summary

**Current State**: 
- 3 main handlers: query-handler, execution-handler, data-management-handler
- 10 existing shared modules in `lambda/shared/`
- Multiple duplicate utility functions across handlers

**Findings**: 
- **15 duplicate functions** identified across handlers
- **~450 lines** of duplicate code that can be consolidated
- **3 new shared modules** recommended: `account_utils.py`, `validation_utils.py`, `drs_server_utils.py`

---

## Existing Shared Modules (10)

1. ✅ `conflict_detection.py` - Server conflict detection, active execution tracking
2. ✅ `cross_account.py` - Cross-account IAM role assumption, DRS client creation
3. ✅ `drs_limits.py` - DRS service limits, wave size validation
4. ✅ `drs_utils.py` - DRS response normalization, field mapping
5. ✅ `execution_utils.py` - Execution state management, progress calculation
6. ✅ `notifications.py` - SNS notification formatting
7. ✅ `rbac_middleware.py` - Role-based access control
8. ✅ `response_utils.py` - API Gateway response formatting, DecimalEncoder
9. ✅ `security_utils.py` - Security headers, input validation
10. ✅ `__init__.py` - Package initialization

---

## Duplicate Functions Analysis

### Category 1: Account Management Functions (HIGH PRIORITY)

**Duplicate Count**: 4 functions
**Total Lines**: ~120 lines
**Handlers Affected**: query-handler, data-management-handler, execution-handler

#### Functions:
1. **`get_current_account_id()`** - 8 lines
   - **Locations**: 
     - query-handler (line 274)
     - data-management-handler (line 3609)
   - **Purpose**: Get current AWS account ID using STS
   - **Usage**: Account context, validation, logging

2. **`get_account_name()`** - 20 lines
   - **Locations**:
     - query-handler (line 284)
     - data-management-handler (line 3619)
   - **Purpose**: Get account alias or name from IAM/Organizations
   - **Usage**: Display names, account identification

3. **`ensure_default_account()`** - 40 lines
   - **Locations**:
     - query-handler (line 308)
     - data-management-handler (line 440)
   - **Purpose**: Auto-initialize current account as default target account
   - **Usage**: First-time setup, account bootstrapping

4. **`get_target_accounts()`** - 50 lines
   - **Locations**:
     - query-handler (line 1122)
     - data-management-handler (line 3641)
   - **Purpose**: List all configured target accounts from DynamoDB
   - **Usage**: Account selection, cross-account operations

**Recommendation**: Create `shared/account_utils.py`

---

### Category 2: Validation Functions (MEDIUM PRIORITY)

**Duplicate Count**: 3 functions
**Total Lines**: ~80 lines
**Handlers Affected**: data-management-handler, execution-handler

#### Functions:
1. **`validate_target_account()`** - 70 lines
   - **Locations**:
     - query-handler (line 1790)
     - data-management-handler (line 3971)
   - **Purpose**: Validate target account access and permissions
   - **Usage**: Account validation, permission checks

2. **`get_active_executions_for_plan()`** - 40 lines
   - **Locations**:
     - execution-handler (line 108)
     - data-management-handler (line 355)
   - **Purpose**: Get active executions for a specific Recovery Plan
   - **Usage**: Conflict detection, plan validation

3. **`response()`** - 10 lines
   - **Locations**:
     - execution-handler (line 77)
     - Already in shared/response_utils.py
   - **Purpose**: Build API Gateway response
   - **Issue**: execution-handler has local copy instead of importing from shared

**Recommendation**: 
- Move `validate_target_account()` to `shared/account_utils.py`
- Move `get_active_executions_for_plan()` to `shared/conflict_detection.py` (already has similar functions)
- Remove local `response()` from execution-handler, import from shared

---

### Category 3: DRS Server Transformation Functions (MEDIUM PRIORITY)

**Duplicate Count**: 2 functions
**Total Lines**: ~150 lines
**Handlers Affected**: query-handler

#### Functions:
1. **`_map_replication_state_to_display()`** - 15 lines
   - **Location**: query-handler (line 355)
   - **Purpose**: Map DRS dataReplicationState to display-friendly state
   - **Usage**: UI display, state normalization
   - **Note**: Similar logic exists in data-management-handler but inline

2. **`_transform_drs_server()`** - 95 lines
   - **Location**: query-handler (line 372)
   - **Purpose**: Transform raw DRS API response to frontend format
   - **Usage**: Server list display, server details

**Recommendation**: Create `shared/drs_server_utils.py` for DRS server transformation utilities

---

### Category 4: Configuration Export/Import Functions (LOW PRIORITY)

**Duplicate Count**: 2 functions
**Total Lines**: ~100 lines
**Handlers Affected**: query-handler, data-management-handler

#### Functions:
1. **`export_configuration()`** - 100 lines
   - **Locations**:
     - query-handler (line 1352)
     - data-management-handler (line 4062)
   - **Purpose**: Export Protection Groups and Recovery Plans to JSON
   - **Usage**: Configuration backup, migration

**Note**: These are actually different implementations:
- query-handler: Read-only export for query operations
- data-management-handler: Full export with import support

**Recommendation**: Keep separate for now, but consider consolidating logic in future

---

### Category 5: Helper Functions Already in Shared (COMPLETED)

**Status**: ✅ Already moved to shared modules

#### Functions:
1. ✅ `query_drs_servers_by_tags()` - in `shared/conflict_detection.py`
2. ✅ `resolve_pg_servers_for_conflict_check()` - in `shared/conflict_detection.py`
3. ✅ `get_servers_in_active_drs_jobs()` - in `shared/conflict_detection.py`
4. ✅ `check_server_conflicts_for_create()` - in `shared/conflict_detection.py`
5. ✅ `check_server_conflicts_for_update()` - in `shared/conflict_detection.py`
6. ✅ `has_circular_dependencies()` - in `shared/conflict_detection.py`

---

## Recommended Actions

### Phase 1: High Priority (Immediate)

**Create `shared/account_utils.py`** - Account management utilities

```python
"""
Account Management Utilities

Centralized account operations for AWS account identification,
validation, and target account management.
"""

def get_current_account_id() -> str:
    """Get current AWS account ID using STS"""
    
def get_account_name(account_id: str) -> Optional[str]:
    """Get account alias or name from IAM/Organizations"""
    
def ensure_default_account() -> None:
    """Auto-initialize current account as default target account"""
    
def get_target_accounts() -> Dict:
    """List all configured target accounts from DynamoDB"""
    
def validate_target_account(account_id: str) -> Dict:
    """Validate target account access and permissions"""
```

**Impact**: 
- Removes ~200 lines of duplicate code
- Centralizes account management logic
- Improves maintainability

---

### Phase 2: Medium Priority (Next Sprint)

**1. Update `shared/conflict_detection.py`**

Add `get_active_executions_for_plan()` function:

```python
def get_active_executions_for_plan(plan_id: str) -> List[Dict]:
    """Get active executions for a specific Recovery Plan"""
```

**2. Create `shared/drs_server_utils.py`** - DRS server transformation utilities

```python
"""
DRS Server Transformation Utilities

Utilities for transforming DRS API responses to frontend format.
"""

def map_replication_state_to_display(replication_state: str) -> str:
    """Map DRS dataReplicationState to display-friendly state"""
    
def transform_drs_server(server: Dict) -> Dict:
    """Transform raw DRS API response to frontend format"""
    
def count_drs_servers(regional_drs) -> Dict:
    """Count DRS source servers and replicating servers"""
```

**3. Fix execution-handler response import**

Remove local `response()` function, import from `shared/response_utils.py`

**Impact**:
- Removes ~250 lines of duplicate code
- Standardizes DRS server transformation
- Improves consistency across handlers

---

### Phase 3: Low Priority (Future)

**Consolidate export/import logic** (if needed)

Consider creating `shared/config_management.py` for configuration export/import operations.

---

## Implementation Plan

### Step 1: Create shared/account_utils.py
1. Create new file with 5 account management functions
2. Update imports in query-handler and data-management-handler
3. Remove duplicate functions from handlers
4. Run tests: `pytest tests/ -v`
5. Deploy: `./scripts/deploy.sh dev --lambda-only`

### Step 2: Update shared/conflict_detection.py
1. Add `get_active_executions_for_plan()` function
2. Update imports in execution-handler and data-management-handler
3. Remove duplicate functions
4. Run tests
5. Deploy

### Step 3: Create shared/drs_server_utils.py
1. Create new file with DRS server transformation functions
2. Update imports in query-handler
3. Remove duplicate functions
4. Run tests
5. Deploy

### Step 4: Fix execution-handler response import
1. Remove local `response()` function
2. Add import from `shared/response_utils.py`
3. Run tests
4. Deploy

---

## Testing Strategy

### Unit Tests
- Test each shared function independently
- Mock AWS API calls (STS, IAM, DynamoDB)
- Verify error handling

### Integration Tests
- Test handlers with shared functions
- Verify cross-handler consistency
- Test account operations end-to-end

### Regression Tests
- Run full test suite after each phase
- Verify no functionality changes
- Check API response formats

---

## Success Metrics

**Code Quality**:
- ✅ Reduce duplicate code by ~450 lines
- ✅ Centralize account management logic
- ✅ Improve code maintainability

**Testing**:
- ✅ Maintain 100% test pass rate
- ✅ Add unit tests for new shared modules
- ✅ Zero regressions

**Deployment**:
- ✅ Deploy to dev environment successfully
- ✅ Verify all handlers work correctly
- ✅ No frontend errors

---

## Risk Assessment

**Low Risk**:
- Account utility functions are simple and well-tested
- Existing shared modules provide proven pattern
- Incremental approach allows rollback

**Mitigation**:
- Test each phase independently
- Deploy to dev environment first
- Monitor CloudWatch logs for errors
- Keep rollback plan ready

---

## Appendix: Function Inventory

### query-handler Functions (30 total)
- `lambda_handler()` - Entry point
- `handle_api_gateway_request()` - API Gateway routing
- `handle_direct_invocation()` - Direct invocation routing
- `_count_drs_servers()` - DRS server counting
- `get_current_account_id()` - **DUPLICATE** → shared/account_utils.py
- `get_account_name()` - **DUPLICATE** → shared/account_utils.py
- `ensure_default_account()` - **DUPLICATE** → shared/account_utils.py
- `_map_replication_state_to_display()` - **MOVE** → shared/drs_server_utils.py
- `_transform_drs_server()` - **MOVE** → shared/drs_server_utils.py
- `get_drs_source_servers()` - Query-specific
- `get_drs_regional_capacity()` - Query-specific
- `get_drs_account_capacity_all_regions()` - Query-specific
- `get_drs_account_capacity_all_regions_response()` - Query-specific
- `validate_concurrent_jobs()` - Query-specific
- `validate_servers_in_all_jobs()` - Query-specific
- `get_drs_account_capacity()` - Query-specific
- `get_target_accounts()` - **DUPLICATE** → shared/account_utils.py
- `get_current_account_info()` - Query-specific
- `export_configuration()` - Query-specific (different from data-management)
- `handle_user_permissions()` - Query-specific
- `handle_user_profile()` - Query-specific
- `handle_user_roles()` - Query-specific
- `get_protection_group_servers()` - Query-specific
- `get_drs_source_server_details()` - Query-specific
- `validate_target_account()` - **DUPLICATE** → shared/account_utils.py

### execution-handler Functions (28 total)
- `response()` - **DUPLICATE** → already in shared/response_utils.py
- `get_cognito_user_from_event()` - Execution-specific
- `get_active_executions_for_plan()` - **DUPLICATE** → shared/conflict_detection.py
- `execute_recovery_plan()` - Execution-specific
- `execute_with_step_functions()` - Execution-specific
- `check_existing_recovery_instances()` - Execution-specific
- `initiate_wave()` - Execution-specific
- `get_server_launch_configurations()` - Execution-specific
- `start_drs_recovery_with_retry()` - Execution-specific
- `start_drs_recovery()` - Execution-specific
- `start_drs_recovery_for_wave()` - Execution-specific
- `execute_recovery_plan_worker()` - Execution-specific
- `list_executions()` - Execution-specific
- `get_execution_details()` - Execution-specific
- `cancel_execution()` - Execution-specific
- `pause_execution()` - Execution-specific
- `lambda_handler()` - Entry point
- `get_execution_details_realtime()` - Execution-specific
- `resume_execution()` - Execution-specific
- `get_recovery_instances()` - Execution-specific
- `terminate_recovery_instances()` - Execution-specific
- `get_termination_job_status()` - Execution-specific
- `get_job_log_items()` - Execution-specific
- `apply_launch_config_to_servers()` - Execution-specific
- `delete_completed_executions()` - Execution-specific

### data-management-handler Functions (50 total)
- `lambda_handler()` - Entry point
- `handle_api_gateway_request()` - API Gateway routing
- `handle_direct_invocation()` - Direct invocation routing
- `get_active_executions_for_plan()` - **DUPLICATE** → shared/conflict_detection.py
- `get_active_execution_for_protection_group()` - Data-management-specific
- `ensure_default_account()` - **DUPLICATE** → shared/account_utils.py
- `validate_unique_pg_name()` - Data-management-specific
- `validate_unique_rp_name()` - Data-management-specific
- `validate_server_replication_states()` - Data-management-specific
- `validate_server_assignments()` - Data-management-specific
- `validate_servers_exist_in_drs()` - Data-management-specific
- `validate_and_get_source_servers()` - Data-management-specific
- `check_tag_conflicts_for_create()` - Data-management-specific
- `check_tag_conflicts_for_update()` - Data-management-specific
- `validate_waves()` - Data-management-specific
- `has_circular_dependencies_by_number()` - Data-management-specific
- `resolve_protection_group_tags()` - Data-management-specific
- `create_protection_group()` - Data-management-specific
- `get_protection_groups()` - Data-management-specific
- `get_protection_group()` - Data-management-specific
- `update_protection_group()` - Data-management-specific
- `delete_protection_group()` - Data-management-specific
- `create_recovery_plan()` - Data-management-specific
- `get_recovery_plans()` - Data-management-specific
- `get_recovery_plan()` - Data-management-specific
- `update_recovery_plan()` - Data-management-specific
- `delete_recovery_plan()` - Data-management-specific
- `handle_drs_tag_sync()` - Data-management-specific
- `sync_tags_in_region()` - Data-management-specific
- `get_tag_sync_settings()` - Data-management-specific
- `update_tag_sync_settings()` - Data-management-specific
- `parse_schedule_expression()` - Data-management-specific
- `import_configuration()` - Data-management-specific
- `_get_existing_protection_groups()` - Data-management-specific
- `_get_existing_recovery_plans()` - Data-management-specific
- `_get_active_execution_servers()` - Data-management-specific
- `_get_all_assigned_servers()` - Data-management-specific
- `_process_protection_group_import()` - Data-management-specific
- `_process_recovery_plan_import()` - Data-management-specific
- `apply_launch_config_to_servers()` - Data-management-specific
- `get_current_account_id()` - **DUPLICATE** → shared/account_utils.py
- `get_account_name()` - **DUPLICATE** → shared/account_utils.py
- `get_target_accounts()` - **DUPLICATE** → shared/account_utils.py
- `get_target_account()` - Data-management-specific
- `create_target_account()` - Data-management-specific
- `update_target_account()` - Data-management-specific
- `delete_target_account()` - Data-management-specific
- `validate_target_account()` - **DUPLICATE** → shared/account_utils.py
- `export_configuration()` - Data-management-specific (different from query)
- `import_configuration()` - Data-management-specific

---

## Summary

**Total Duplicate Functions**: 15
**Total Duplicate Lines**: ~450 lines
**Recommended New Shared Modules**: 3
- `shared/account_utils.py` (5 functions, ~200 lines)
- `shared/drs_server_utils.py` (3 functions, ~150 lines)
- Update `shared/conflict_detection.py` (1 function, ~40 lines)

**Implementation Effort**: 
- Phase 1 (High Priority): 4-6 hours
- Phase 2 (Medium Priority): 4-6 hours
- Phase 3 (Low Priority): 2-4 hours
- **Total**: 10-16 hours

**Benefits**:
- Reduced code duplication by ~450 lines
- Centralized account management logic
- Improved maintainability and consistency
- Easier testing and debugging
