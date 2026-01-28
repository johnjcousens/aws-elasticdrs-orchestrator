# API Endpoint Audit

## Executive Summary

**Total Endpoints**: 48 (production endpoints used by frontend)
**Unused Endpoints**: 5 (duplicates/unused - marked for removal)
**Status**: Documentation updated, cleanup task created

## Production Endpoints (48)

### Query Handler (13 endpoints)
**File**: `lambda/query-handler/index.py`

1. `GET /drs/source-servers` - List DRS source servers
2. `GET /drs/quotas` - Get DRS service limits
3. `GET /ec2/subnets` - List EC2 subnets
4. `GET /ec2/security-groups` - List security groups
5. `GET /ec2/instance-profiles` - List IAM instance profiles
6. `GET /ec2/instance-types` - List EC2 instance types
7. `GET /accounts/current` - Get current account info
8. `GET /config/export` - Export configuration
9. `GET /user/permissions` - Get user permissions
10. `GET /config/tag-sync` - Get tag sync settings ✅ ADDED
11. `GET /drs/service-limits` - Get DRS service limits (alias for /drs/quotas)

### Data Management Handler (21 endpoints)
**File**: `lambda/data-management-handler/index.py`

**Protection Groups (6)**:
12. `GET /protection-groups` - List protection groups
13. `POST /protection-groups` - Create protection group
14. `POST /protection-groups/resolve` - Preview tag-based servers
15. `GET /protection-groups/{id}` - Get protection group
16. `PUT /protection-groups/{id}` - Update protection group
17. `DELETE /protection-groups/{id}` - Delete protection group

**Recovery Plans (6)**:
18. `GET /recovery-plans` - List recovery plans
19. `POST /recovery-plans` - Create recovery plan
20. `GET /recovery-plans/{id}` - Get recovery plan
21. `PUT /recovery-plans/{id}` - Update recovery plan
22. `DELETE /recovery-plans/{id}` - Delete recovery plan
23. `GET /recovery-plans/{id}/check-existing-instances` - Check existing instances

**Tag Sync & Config (4)**:
24. `POST /drs/tag-sync` - Manual tag synchronization ✅ ADDED
25. `PUT /config/tag-sync` - Update tag sync settings ✅ ADDED
26. `POST /config/import` - Import configuration

**Target Accounts (5)**:
27. `GET /accounts/targets` - List target accounts
28. `POST /accounts/targets` - Create target account
29. `GET /accounts/targets/{id}` - Get target account
30. `PUT /accounts/targets/{id}` - Update target account
31. `DELETE /accounts/targets/{id}` - Delete target account
32. `POST /accounts/targets/{id}/validate` - Validate target account ✅ ADDED

### Execution Handler (12 endpoints)
**File**: `lambda/execution-handler/index.py`

**Executions (10)**:
33. `GET /executions` - List executions
34. `POST /executions` - Start execution
35. `DELETE /executions` - Bulk delete executions
36. `GET /executions/{executionId}` - Get execution details
37. `POST /executions/{executionId}/cancel` - Cancel execution
38. `POST /executions/{executionId}/pause` - Pause execution
39. `POST /executions/{executionId}/resume` - Resume execution
40. `POST /executions/{executionId}/terminate-instances` - Terminate recovery instances
41. `GET /executions/{executionId}/job-logs` - Get DRS job logs
42. `GET /executions/{executionId}/termination-status` - Get termination status

**Recovery Instances (2)**:
43. `GET /executions/{executionId}/recovery-instances` - List recovery instances
44. `POST /recovery-plans/{id}/execute` - Execute recovery plan

### Public Endpoints (2)
45. `GET /health` - Health check
46. `OPTIONS *` - CORS preflight

## Unused Endpoints (5) - Marked for Removal

### ❌ Duplicates
1. `GET /drs/accounts` - Duplicate of `/accounts/targets` (frontend uses `/accounts/targets`)
2. `GET /drs/service-limits` - Duplicate of `/drs/quotas` (frontend uses `/drs/quotas`)
3. `POST /executions/delete` - Duplicate of `DELETE /executions` (frontend uses DELETE)

### ❌ Unused
4. `GET /user/profile` - Not used by frontend (permissions endpoint provides enough)
5. `GET /user/roles` - Not used by frontend (permissions endpoint includes roles)

## Endpoint Categories (48 Total)

### Account Management (7)
- `/accounts/current` (GET)
- `/accounts/targets` (GET, POST)
- `/accounts/targets/{id}` (GET, PUT, DELETE)
- `/accounts/targets/{id}/validate` (POST) ✅

### Protection Groups (6)
- `/protection-groups` (GET, POST)
- `/protection-groups/resolve` (POST)
- `/protection-groups/{id}` (GET, PUT, DELETE)

### Recovery Plans (7)
- `/recovery-plans` (GET, POST)
- `/recovery-plans/{id}` (GET, PUT, DELETE)
- `/recovery-plans/{id}/execute` (POST)
- `/recovery-plans/{id}/check-existing-instances` (GET)

### Executions (12)
- `/executions` (GET, POST, DELETE)
- `/executions/{executionId}` (GET)
- `/executions/{executionId}/cancel` (POST)
- `/executions/{executionId}/pause` (POST)
- `/executions/{executionId}/resume` (POST)
- `/executions/{executionId}/terminate-instances` (POST)
- `/executions/{executionId}/job-logs` (GET)
- `/executions/{executionId}/termination-status` (GET)
- `/executions/{executionId}/recovery-instances` (GET)

### DRS Operations (3)
- `/drs/source-servers` (GET)
- `/drs/quotas` (GET)
- `/drs/tag-sync` (POST) ✅

### EC2 Resources (4)
- `/ec2/subnets` (GET)
- `/ec2/security-groups` (GET)
- `/ec2/instance-profiles` (GET)
- `/ec2/instance-types` (GET)

### Configuration (4)
- `/config/export` (GET)
- `/config/import` (POST)
- `/config/tag-sync` (GET, PUT) ✅

### User Management (1)
- `/user/permissions` (GET)

### System (2)
- `/health` (GET)
- `OPTIONS *` (CORS)

## Documentation Status

### ✅ Updated
- `PRODUCT_REQUIREMENTS_DOCUMENT.md` - Updated to 48 endpoints
- `ENDPOINT_AUDIT.md` - Complete inventory

### 📋 Pending
- `SOFTWARE_REQUIREMENTS_SPECIFICATION.md` - Needs endpoint updates
- Backend cleanup - Remove 5 unused endpoints

## Next Steps

1. **Update SRS** - Add 4 missing endpoints to technical specification
2. **Backend Cleanup** - Remove 5 unused/duplicate endpoints (see ENDPOINT_CLEANUP_TASK.md)
3. **RBAC Verification** - Ensure all 48 endpoints have permission mappings
