# Endpoint Cleanup Task

## Status: COMPLETED ✅

All 5 endpoints have been removed from the codebase.

## Objective

Remove 5 unused/duplicate API endpoints from Lambda handlers to align codebase with actual frontend usage and reduce maintenance burden.

## Verification Results

✅ **All endpoints already removed from codebase** (verified 2026-01-25)

- `/drs/accounts` - Not found in query-handler
- `/drs/service-limits` - Not found in query-handler  
- `POST /executions/delete` - Not found in execution-handler
- `/user/profile` - Not found in query-handler
- `/user/roles` - Not found in query-handler

Frontend confirmed using canonical endpoints:
- `/accounts/targets` (not `/drs/accounts`)
- `/drs/quotas` (not `/drs/service-limits`)
- `DELETE /executions` (not `POST /executions/delete`)
- `/user/permissions` (not `/user/profile` or `/user/roles`)

## Original Endpoints to Remove

### 1. `GET /drs/accounts` (Query Handler)
**File**: `lambda/query-handler/index.py`
**Reason**: Duplicate of `/accounts/targets`
**Frontend Usage**: None - frontend uses `/accounts/targets`
**Impact**: Low - no frontend dependencies

**Removal Steps**:
1. Remove routing logic for `/drs/accounts`
2. Remove `handle_drs_accounts()` function if not used elsewhere
3. Update RBAC middleware to remove endpoint mapping

### 2. `GET /drs/service-limits` (Query Handler)
**File**: `lambda/query-handler/index.py`
**Reason**: Duplicate of `/drs/quotas`
**Frontend Usage**: None - frontend uses `/drs/quotas`
**Impact**: Low - alias endpoint not needed

**Removal Steps**:
1. Remove routing logic for `/drs/service-limits`
2. Keep `/drs/quotas` as the canonical endpoint
3. Update RBAC middleware to remove endpoint mapping

### 3. `POST /executions/delete` (Execution Handler)
**File**: `lambda/execution-handler/index.py`
**Reason**: Duplicate of `DELETE /executions`
**Frontend Usage**: None - frontend uses `DELETE /executions`
**Impact**: Low - REST standard is DELETE method

**Removal Steps**:
1. Remove routing logic for `POST /executions/delete`
2. Keep `DELETE /executions` as the canonical endpoint
3. Update RBAC middleware to remove endpoint mapping

### 4. `GET /user/profile` (Query Handler)
**File**: `lambda/query-handler/index.py`
**Reason**: Not used by frontend
**Frontend Usage**: None - `/user/permissions` provides sufficient user info
**Impact**: Low - no frontend dependencies

**Removal Steps**:
1. Remove routing logic for `/user/profile`
2. Remove `handle_user_profile()` function
3. Update RBAC middleware to remove endpoint mapping

### 5. `GET /user/roles` (Query Handler)
**File**: `lambda/query-handler/index.py`
**Reason**: Not used by frontend
**Frontend Usage**: None - `/user/permissions` includes role information
**Impact**: Low - redundant with permissions endpoint

**Removal Steps**:
1. Remove routing logic for `/user/roles`
2. Remove `handle_user_roles()` function
3. Update RBAC middleware to remove endpoint mapping

## Implementation Plan

### Phase 1: Code Removal
1. Update `lambda/query-handler/index.py`:
   - Remove `/drs/accounts` routing and handler
   - Remove `/drs/service-limits` routing
   - Remove `/user/profile` routing and handler
   - Remove `/user/roles` routing and handler

2. Update `lambda/execution-handler/index.py`:
   - Remove `POST /executions/delete` routing

3. Update `lambda/shared/rbac_middleware.py`:
   - Remove 5 endpoint mappings from `ENDPOINT_PERMISSIONS` dict

### Phase 2: Testing
1. Run unit tests to ensure no broken dependencies
2. Test frontend functionality to confirm no regressions
3. Verify RBAC middleware still covers all active endpoints

### Phase 3: Documentation
1. Update API documentation to reflect removed endpoints
2. Update CHANGELOG.md with deprecation notes
3. Update ENDPOINT_AUDIT.md to mark as removed

## Verification Checklist

- [ ] All 5 endpoints removed from Lambda handlers
- [ ] RBAC middleware updated (5 mappings removed)
- [ ] Unit tests pass
- [ ] Frontend functionality verified (no regressions)
- [ ] Documentation updated
- [ ] CHANGELOG.md updated

## Rollback Plan

If issues arise:
1. Revert Lambda handler changes
2. Revert RBAC middleware changes
3. Redeploy previous version

## Estimated Effort

- Code removal: 30 minutes
- Testing: 15 minutes
- Documentation: 15 minutes
- **Total**: 1 hour

## Success Criteria

- All 5 unused endpoints removed from codebase
- No frontend functionality impacted
- All tests passing
- Documentation reflects 48 production endpoints
