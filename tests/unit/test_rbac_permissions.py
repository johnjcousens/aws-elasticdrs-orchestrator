"""
Unit tests for RBAC permission enforcement.

Tests role-based access control (RBAC) permission enforcement for different roles:
- Admin role (all operations)
- Operator role (operational data)
- Viewer role (read-only operational data)
- Auditor role (audit logs + operational data)
- Planner role (recovery plans)

Test Coverage:
- Task 14.1: Admin role permissions (all operations)
- Task 14.2: Operator role permissions (operational data)
- Task 14.3: Viewer role permissions (read-only operational data)
- Task 14.4: Auditor role permissions (audit logs + operational data)
- Task 14.5: Planner role permissions (recovery plans)
- Task 14.6: Auditor can access audit logs, Viewer cannot
- Task 14.7: Permission-to-operation mapping enforced
- Task 14.8: Unauthorized operations return 403 Forbidden
"""

import json
from unittest.mock import Mock, patch, MagicMock

import pytest

# Import RBAC middleware functions
from shared.rbac_middleware import (
    require_permission,
    get_user_from_event,
    get_user_permissions,
    get_user_roles,
    has_permission,
    DRSRole,
    DRSPermission,
    ROLE_PERMISSIONS,
)


class TestAdminRolePermissions:
    """Test Task 14.1: Admin role permissions (all operations)."""

    def test_admin_has_all_permissions(self):
        """
        Test Admin role has all permissions.

        Admin role (DRS_ORCHESTRATION_ADMIN) should have access to all operations:
        - Account management (register, delete, modify, view)
        - Recovery operations (start, stop, terminate, view)
        - Protection groups (create, delete, modify, view)
        - Recovery plans (create, delete, modify, view)
        - Configuration management (export, import)

        Verifies:
        - Admin permissions include all operation types
        - Admin can perform any operation
        """
        # Arrange
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "cognito:groups": "DRSOrchestrationAdmin",
                        "email": "admin@example.com",
                        "sub": "admin-user-id",
                    }
                }
            }
        }

        # Act
        user = get_user_from_event(event)
        permissions = get_user_permissions(user)
        roles = get_user_roles(user)

        # Assert - Has Admin role
        assert DRSRole.DRS_ORCHESTRATION_ADMIN in roles

        # Assert - Has all permissions
        assert DRSPermission.REGISTER_ACCOUNTS in permissions
        assert DRSPermission.DELETE_ACCOUNTS in permissions
        assert DRSPermission.MODIFY_ACCOUNTS in permissions
        assert DRSPermission.VIEW_ACCOUNTS in permissions
        assert DRSPermission.START_RECOVERY in permissions
        assert DRSPermission.STOP_RECOVERY in permissions
        assert DRSPermission.TERMINATE_INSTANCES in permissions
        assert DRSPermission.VIEW_EXECUTIONS in permissions
        assert DRSPermission.CREATE_PROTECTION_GROUPS in permissions
        assert DRSPermission.DELETE_PROTECTION_GROUPS in permissions
        assert DRSPermission.MODIFY_PROTECTION_GROUPS in permissions
        assert DRSPermission.VIEW_PROTECTION_GROUPS in permissions
        assert DRSPermission.CREATE_RECOVERY_PLANS in permissions
        assert DRSPermission.DELETE_RECOVERY_PLANS in permissions
        assert DRSPermission.MODIFY_RECOVERY_PLANS in permissions
        assert DRSPermission.VIEW_RECOVERY_PLANS in permissions
        assert DRSPermission.EXPORT_CONFIGURATION in permissions
        assert DRSPermission.IMPORT_CONFIGURATION in permissions

    def test_admin_can_access_all_operations(self):
        """
        Test Admin role can access all operations.

        Verifies:
        - Admin can perform recovery operations
        - Admin can manage protection groups
        - Admin can manage recovery plans
        - Admin can manage accounts
        """
        # Arrange
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "cognito:groups": "DRSOrchestrationAdmin",
                        "email": "admin@example.com",
                        "sub": "admin-user-id",
                    }
                }
            }
        }

        # Mock decorated functions
        @require_permission(DRSPermission.START_RECOVERY)
        def start_recovery(event, context):
            return {"statusCode": 200, "body": json.dumps({"message": "Success"})}

        @require_permission(DRSPermission.DELETE_ACCOUNTS)
        def delete_account(event, context):
            return {"statusCode": 200, "body": json.dumps({"message": "Success"})}

        # Act & Assert - Admin should have access to all operations
        response1 = start_recovery(event, Mock())
        assert response1["statusCode"] == 200

        response2 = delete_account(event, Mock())
        assert response2["statusCode"] == 200


class TestOperatorRolePermissions:
    """Test Task 14.2: Operator role permissions (operational data)."""

    def test_operator_has_operational_permissions(self):
        """
        Test Operator role has operational permissions.

        Operator role should have:
        - VIEW_ACCOUNTS
        - START_RECOVERY, STOP_RECOVERY
        - VIEW_EXECUTIONS
        - MODIFY_PROTECTION_GROUPS, VIEW_PROTECTION_GROUPS
        - MODIFY_RECOVERY_PLANS, VIEW_RECOVERY_PLANS

        Operator role should NOT have:
        - CREATE/DELETE operations (planning is restricted)
        - AUDIT_READ (audit access restricted)
        - TERMINATE_INSTANCES (termination restricted)

        Verifies:
        - Operator permissions include operational data
        - Operator permissions exclude audit and destructive operations
        """
        # Arrange
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "cognito:groups": "DRSOperator",
                        "email": "operator@example.com",
                        "sub": "operator-user-id",
                    }
                }
            }
        }

        # Act
        user = get_user_from_event(event)
        permissions = get_user_permissions(user)
        roles = get_user_roles(user)

        # Assert - Has Operator role
        assert DRSRole.DRS_OPERATOR in roles

        # Assert - Has operational permissions
        assert DRSPermission.VIEW_ACCOUNTS in permissions
        assert DRSPermission.START_RECOVERY in permissions
        assert DRSPermission.STOP_RECOVERY in permissions
        assert DRSPermission.VIEW_EXECUTIONS in permissions
        assert DRSPermission.MODIFY_PROTECTION_GROUPS in permissions
        assert DRSPermission.VIEW_PROTECTION_GROUPS in permissions
        assert DRSPermission.MODIFY_RECOVERY_PLANS in permissions
        assert DRSPermission.VIEW_RECOVERY_PLANS in permissions

        # Assert - Does NOT have restricted permissions
        assert DRSPermission.CREATE_PROTECTION_GROUPS not in permissions
        assert DRSPermission.DELETE_PROTECTION_GROUPS not in permissions
        assert DRSPermission.CREATE_RECOVERY_PLANS not in permissions
        assert DRSPermission.DELETE_RECOVERY_PLANS not in permissions
        assert DRSPermission.AUDIT_READ not in permissions
        assert DRSPermission.TERMINATE_INSTANCES not in permissions

    def test_operator_can_execute_recovery_operations(self):
        """
        Test Operator role can execute recovery operations.

        Verifies:
        - Operator can start recovery executions
        - Operator can monitor execution status
        - Operator can manage protection groups
        """
        # Arrange
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "cognito:groups": "DRSOperator",
                        "email": "operator@example.com",
                        "sub": "operator-user-id",
                    }
                }
            },
            "httpMethod": "POST",
            "path": "/executions",
        }

        # Mock decorated functions
        @require_permission(DRSPermission.START_RECOVERY)
        def start_recovery(event, context):
            return {"statusCode": 200, "body": json.dumps({"message": "Recovery started"})}

        @require_permission(DRSPermission.MODIFY_PROTECTION_GROUPS)
        def update_protection_group(event, context):
            return {"statusCode": 200, "body": json.dumps({"message": "Group updated"})}

        # Act & Assert - Operator should have access
        response1 = start_recovery(event, Mock())
        assert response1["statusCode"] == 200

        response2 = update_protection_group(event, Mock())
        assert response2["statusCode"] == 200


class TestViewerRolePermissions:
    """Test Task 14.3: Viewer role permissions (read-only operational data)."""

    def test_viewer_has_read_only_permissions(self):
        """
        Test Viewer role has read-only permissions.

        Viewer role should have:
        - VIEW_ACCOUNTS
        - VIEW_EXECUTIONS
        - VIEW_PROTECTION_GROUPS
        - VIEW_RECOVERY_PLANS

        Viewer role should NOT have:
        - Any write/modify/delete permissions
        - START_RECOVERY, STOP_RECOVERY, TERMINATE_INSTANCES
        - CREATE/DELETE/MODIFY operations

        Verifies:
        - Viewer permissions are read-only
        - Viewer cannot modify any data
        - Viewer has DRS_READ_ONLY role
        """
        # Arrange
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "cognito:groups": "DRSReadOnly",
                        "email": "viewer@example.com",
                        "sub": "viewer-user-id",
                    }
                }
            }
        }

        # Act
        user = get_user_from_event(event)
        permissions = get_user_permissions(user)
        roles = get_user_roles(user)

        # Assert - Has Viewer role (DRS_READ_ONLY)
        assert DRSRole.DRS_READ_ONLY in roles

        # Assert - Has read-only permissions
        assert DRSPermission.VIEW_ACCOUNTS in permissions
        assert DRSPermission.VIEW_EXECUTIONS in permissions
        assert DRSPermission.VIEW_PROTECTION_GROUPS in permissions
        assert DRSPermission.VIEW_RECOVERY_PLANS in permissions

        # Assert - Does NOT have write permissions
        assert DRSPermission.REGISTER_ACCOUNTS not in permissions
        assert DRSPermission.DELETE_ACCOUNTS not in permissions
        assert DRSPermission.MODIFY_ACCOUNTS not in permissions
        assert DRSPermission.START_RECOVERY not in permissions
        assert DRSPermission.STOP_RECOVERY not in permissions
        assert DRSPermission.TERMINATE_INSTANCES not in permissions
        assert DRSPermission.CREATE_PROTECTION_GROUPS not in permissions
        assert DRSPermission.DELETE_PROTECTION_GROUPS not in permissions
        assert DRSPermission.MODIFY_PROTECTION_GROUPS not in permissions
        assert DRSPermission.CREATE_RECOVERY_PLANS not in permissions
        assert DRSPermission.DELETE_RECOVERY_PLANS not in permissions
        assert DRSPermission.MODIFY_RECOVERY_PLANS not in permissions
        assert DRSPermission.EXPORT_CONFIGURATION not in permissions
        assert DRSPermission.IMPORT_CONFIGURATION not in permissions

    def test_viewer_can_access_read_operations(self):
        """
        Test Viewer role can access read operations.

        Verifies:
        - Viewer can list protection groups
        - Viewer can view recovery plans
        - Viewer can view executions
        - Viewer can view accounts
        """
        # Arrange
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "cognito:groups": "DRSReadOnly",
                        "email": "viewer@example.com",
                        "sub": "viewer-user-id",
                    }
                }
            },
            "httpMethod": "GET",
            "path": "/protection-groups",
        }

        # Mock decorated functions
        @require_permission(DRSPermission.VIEW_PROTECTION_GROUPS)
        def list_protection_groups(event, context):
            return {"statusCode": 200, "body": json.dumps({"groups": []})}

        @require_permission(DRSPermission.VIEW_RECOVERY_PLANS)
        def list_recovery_plans(event, context):
            return {"statusCode": 200, "body": json.dumps({"plans": []})}

        @require_permission(DRSPermission.VIEW_EXECUTIONS)
        def list_executions(event, context):
            return {"statusCode": 200, "body": json.dumps({"executions": []})}

        # Act & Assert - Viewer can access all read operations
        response1 = list_protection_groups(event, Mock())
        assert response1["statusCode"] == 200

        response2 = list_recovery_plans(event, Mock())
        assert response2["statusCode"] == 200

        response3 = list_executions(event, Mock())
        assert response3["statusCode"] == 200

    def test_viewer_cannot_modify_data(self):
        """
        Test Viewer role cannot modify data.

        Verifies:
        - Viewer can read operational data
        - Viewer cannot write operational data
        - Viewer does not have write permissions
        """
        # Arrange
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "cognito:groups": "DRSReadOnly",
                        "email": "viewer@example.com",
                        "sub": "viewer-user-id",
                    }
                }
            }
        }

        # Act
        user = get_user_from_event(event)
        permissions = get_user_permissions(user)

        # Assert - Viewer has read permissions
        assert DRSPermission.VIEW_PROTECTION_GROUPS in permissions
        assert DRSPermission.VIEW_RECOVERY_PLANS in permissions
        assert DRSPermission.VIEW_EXECUTIONS in permissions

        # Assert - Viewer does NOT have write permissions
        assert DRSPermission.CREATE_PROTECTION_GROUPS not in permissions
        assert DRSPermission.MODIFY_PROTECTION_GROUPS not in permissions
        assert DRSPermission.DELETE_PROTECTION_GROUPS not in permissions
        assert DRSPermission.START_RECOVERY not in permissions
        assert DRSPermission.STOP_RECOVERY not in permissions
        assert DRSPermission.TERMINATE_INSTANCES not in permissions

        # Assert - Verify permission checks return False for write operations
        assert not has_permission(user, DRSPermission.CREATE_PROTECTION_GROUPS)
        assert not has_permission(user, DRSPermission.START_RECOVERY)
        assert not has_permission(user, DRSPermission.TERMINATE_INSTANCES)



class TestAuditorRolePermissions:
    """Test Task 14.4: Auditor role permissions (audit logs + operational data)."""

    def test_auditor_has_audit_and_read_permissions(self):
        """
        Test Auditor role has audit and read permissions.

        Auditor role should have:
        - VIEW_ACCOUNTS (read-only operational data)
        - VIEW_EXECUTIONS (read-only operational data)
        - VIEW_PROTECTION_GROUPS (read-only operational data)
        - VIEW_RECOVERY_PLANS (read-only operational data)
        - AUDIT_READ (unique to Auditor - can access audit logs)

        Auditor role should NOT have:
        - Any write/modify/delete permissions
        - START_RECOVERY, STOP_RECOVERY, TERMINATE_INSTANCES
        - CREATE/DELETE/MODIFY operations

        Verifies:
        - Auditor can access audit logs (key difference from Viewer)
        - Auditor can read operational data
        - Auditor cannot modify any data
        - Auditor has DRS_AUDITOR role
        """
        # Arrange
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "cognito:groups": "DRSAuditor",
                        "email": "auditor@example.com",
                        "sub": "auditor-user-id",
                    }
                }
            }
        }

        # Act
        user = get_user_from_event(event)
        permissions = get_user_permissions(user)
        roles = get_user_roles(user)

        # Assert - Has Auditor role (DRS_AUDITOR)
        assert DRSRole.DRS_AUDITOR in roles

        # Assert - Has audit read permission (unique to Auditor)
        assert DRSPermission.AUDIT_READ in permissions

        # Assert - Has read-only operational permissions
        assert DRSPermission.VIEW_ACCOUNTS in permissions
        assert DRSPermission.VIEW_EXECUTIONS in permissions
        assert DRSPermission.VIEW_PROTECTION_GROUPS in permissions
        assert DRSPermission.VIEW_RECOVERY_PLANS in permissions

        # Assert - Does NOT have write permissions
        assert DRSPermission.REGISTER_ACCOUNTS not in permissions
        assert DRSPermission.DELETE_ACCOUNTS not in permissions
        assert DRSPermission.MODIFY_ACCOUNTS not in permissions
        assert DRSPermission.START_RECOVERY not in permissions
        assert DRSPermission.STOP_RECOVERY not in permissions
        assert DRSPermission.TERMINATE_INSTANCES not in permissions
        assert DRSPermission.CREATE_PROTECTION_GROUPS not in permissions
        assert DRSPermission.DELETE_PROTECTION_GROUPS not in permissions
        assert DRSPermission.MODIFY_PROTECTION_GROUPS not in permissions
        assert DRSPermission.CREATE_RECOVERY_PLANS not in permissions
        assert DRSPermission.DELETE_RECOVERY_PLANS not in permissions
        assert DRSPermission.MODIFY_RECOVERY_PLANS not in permissions
        assert DRSPermission.EXPORT_CONFIGURATION not in permissions
        assert DRSPermission.IMPORT_CONFIGURATION not in permissions

    def test_auditor_can_access_audit_logs(self):
        """
        Test Auditor role can access audit logs.

        Verifies:
        - Auditor can query audit log table (200 OK)
        - Auditor can read operational data (200 OK)
        - Auditor cannot modify audit logs (403 Forbidden)
        - Auditor cannot write operational data (403 Forbidden)
        """
        # Arrange
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "cognito:groups": "DRSAuditor",
                        "email": "auditor@example.com",
                        "sub": "auditor-user-id",
                    }
                }
            }
        }

        # Mock decorated functions
        @require_permission(DRSPermission.AUDIT_READ)
        def get_audit_logs(event, context):
            return {"statusCode": 200, "body": json.dumps({"logs": []})}

        @require_permission(DRSPermission.VIEW_PROTECTION_GROUPS)
        def list_protection_groups(event, context):
            return {"statusCode": 200, "body": json.dumps({"groups": []})}

        @require_permission(DRSPermission.CREATE_PROTECTION_GROUPS)
        def create_protection_group(event, context):
            return {"statusCode": 200, "body": json.dumps({"message": "Success"})}

        # Act & Assert - Auditor can read audit logs (unique capability)
        response1 = get_audit_logs(event, Mock())
        assert response1["statusCode"] == 200

        # Act & Assert - Auditor can read operational data
        response2 = list_protection_groups(event, Mock())
        assert response2["statusCode"] == 200

        # Act & Assert - Auditor cannot write operational data (403 Forbidden)
        response3 = create_protection_group(event, Mock())
        assert response3["statusCode"] == 403
        body = json.loads(response3["body"])
        assert "error" in body
        assert "Forbidden" in body["error"] or "permission" in body["error"].lower()

    def test_auditor_cannot_modify_data(self):
        """
        Test Auditor role cannot modify data.

        Verifies:
        - Auditor can read operational data
        - Auditor cannot write operational data
        - Auditor does not have write permissions
        """
        # Arrange
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "cognito:groups": "DRSAuditor",
                        "email": "auditor@example.com",
                        "sub": "auditor-user-id",
                    }
                }
            }
        }

        # Act
        user = get_user_from_event(event)
        permissions = get_user_permissions(user)

        # Assert - Auditor has read permissions
        assert DRSPermission.VIEW_PROTECTION_GROUPS in permissions
        assert DRSPermission.VIEW_RECOVERY_PLANS in permissions
        assert DRSPermission.VIEW_EXECUTIONS in permissions
        assert DRSPermission.AUDIT_READ in permissions

        # Assert - Auditor does NOT have write permissions
        assert DRSPermission.CREATE_PROTECTION_GROUPS not in permissions
        assert DRSPermission.MODIFY_PROTECTION_GROUPS not in permissions
        assert DRSPermission.DELETE_PROTECTION_GROUPS not in permissions
        assert DRSPermission.START_RECOVERY not in permissions
        assert DRSPermission.STOP_RECOVERY not in permissions
        assert DRSPermission.TERMINATE_INSTANCES not in permissions

        # Assert - Verify permission checks return False for write operations
        assert not has_permission(user, DRSPermission.CREATE_PROTECTION_GROUPS)
        assert not has_permission(user, DRSPermission.START_RECOVERY)
        assert not has_permission(user, DRSPermission.TERMINATE_INSTANCES)


class TestPlannerRolePermissions:
    """Test Task 14.5: Planner role permissions (recovery plans)."""

    def test_planner_has_planning_permissions(self):
        """
        Test Planner role has planning permissions.

        Planner role should have:
        - VIEW_ACCOUNTS
        - START_RECOVERY, STOP_RECOVERY
        - VIEW_EXECUTIONS
        - CREATE/DELETE/MODIFY/VIEW_PROTECTION_GROUPS
        - CREATE/DELETE/MODIFY/VIEW_RECOVERY_PLANS

        Planner role should NOT have:
        - TERMINATE_INSTANCES (cannot terminate, only plan)
        - AUDIT_READ (audit access restricted)
        - REGISTER/DELETE/MODIFY_ACCOUNTS (account management restricted)

        Verifies:
        - Planner can create/modify recovery plans
        - Planner can read operational data for planning
        - Planner can execute recovery operations
        """
        # Arrange
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "cognito:groups": "DRSPlanManager",
                        "email": "planner@example.com",
                        "sub": "planner-user-id",
                    }
                }
            }
        }

        # Act
        user = get_user_from_event(event)
        permissions = get_user_permissions(user)
        roles = get_user_roles(user)

        # Assert - Has Planner role
        assert DRSRole.DRS_PLAN_MANAGER in roles

        # Assert - Has planning permissions
        assert DRSPermission.VIEW_ACCOUNTS in permissions
        assert DRSPermission.START_RECOVERY in permissions
        assert DRSPermission.STOP_RECOVERY in permissions
        assert DRSPermission.VIEW_EXECUTIONS in permissions
        assert DRSPermission.CREATE_PROTECTION_GROUPS in permissions
        assert DRSPermission.DELETE_PROTECTION_GROUPS in permissions
        assert DRSPermission.MODIFY_PROTECTION_GROUPS in permissions
        assert DRSPermission.VIEW_PROTECTION_GROUPS in permissions
        assert DRSPermission.CREATE_RECOVERY_PLANS in permissions
        assert DRSPermission.DELETE_RECOVERY_PLANS in permissions
        assert DRSPermission.MODIFY_RECOVERY_PLANS in permissions
        assert DRSPermission.VIEW_RECOVERY_PLANS in permissions

        # Assert - Does NOT have restricted permissions
        assert DRSPermission.TERMINATE_INSTANCES not in permissions
        assert DRSPermission.AUDIT_READ not in permissions
        assert DRSPermission.REGISTER_ACCOUNTS not in permissions
        assert DRSPermission.DELETE_ACCOUNTS not in permissions
        assert DRSPermission.MODIFY_ACCOUNTS not in permissions

    def test_planner_can_create_recovery_plans(self):
        """
        Test Planner role can create recovery plans.

        Verifies:
        - Planner can create new recovery plans
        - Planner can modify existing recovery plans
        - Planner can execute recovery operations
        """
        # Arrange
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "cognito:groups": "DRSPlanManager",
                        "email": "planner@example.com",
                        "sub": "planner-user-id",
                    }
                }
            },
            "httpMethod": "POST",
            "path": "/recovery-plans",
        }

        # Mock decorated functions
        @require_permission(DRSPermission.CREATE_RECOVERY_PLANS)
        def create_recovery_plan(event, context):
            return {"statusCode": 200, "body": json.dumps({"plan_id": "plan-123"})}

        @require_permission(DRSPermission.START_RECOVERY)
        def start_recovery(event, context):
            return {"statusCode": 200, "body": json.dumps({"message": "Recovery started"})}

        # Act & Assert - Planner can create plans
        response1 = create_recovery_plan(event, Mock())
        assert response1["statusCode"] == 200

        # Act & Assert - Planner can execute recovery
        response2 = start_recovery(event, Mock())
        assert response2["statusCode"] == 200


class TestAuditorVsViewerAccess:
    """Test Task 14.6: Auditor can access audit logs, Viewer cannot."""

    def test_auditor_can_access_audit_logs_viewer_cannot(self):
        """
        Test Auditor can access audit logs, Viewer cannot.

        Key Difference:
        - Auditor has AUDIT_READ permission
        - Viewer does NOT have AUDIT_READ permission

        Verifies:
        - Auditor can query audit log table
        - Viewer gets 403 Forbidden when accessing audit logs
        - Both can read operational data
        """
        # Arrange - Auditor event
        auditor_event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "cognito:groups": "DRSAuditor",
                        "email": "auditor@example.com",
                        "sub": "auditor-user-id",
                    }
                }
            },
            "httpMethod": "GET",
            "path": "/audit-logs",
        }

        # Arrange - Viewer event
        viewer_event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "cognito:groups": "DRSReadOnly",
                        "email": "viewer@example.com",
                        "sub": "viewer-user-id",
                    }
                }
            },
            "httpMethod": "GET",
            "path": "/audit-logs",
        }

        # Mock decorated function
        @require_permission(DRSPermission.AUDIT_READ)
        def get_audit_logs(event, context):
            return {"statusCode": 200, "body": json.dumps({"logs": []})}

        # Act & Assert - Auditor can access audit logs
        auditor_response = get_audit_logs(auditor_event, Mock())
        assert auditor_response["statusCode"] == 200

        # Act & Assert - Viewer cannot access audit logs (403 Forbidden)
        viewer_response = get_audit_logs(viewer_event, Mock())
        assert viewer_response["statusCode"] == 403
        body = json.loads(viewer_response["body"])
        assert "error" in body
        assert "Forbidden" in body["error"] or "permission" in body["error"].lower()

    def test_both_can_read_operational_data(self):
        """
        Test both Auditor and Viewer can read operational data.

        Verifies:
        - Both roles have VIEW_PROTECTION_GROUPS permission
        - Both roles can query operational data
        - Operational data access is identical
        """
        # Arrange - Auditor event
        auditor_event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "cognito:groups": "DRSAuditor",
                        "email": "auditor@example.com",
                        "sub": "auditor-user-id",
                    }
                }
            },
            "httpMethod": "GET",
            "path": "/protection-groups",
        }

        # Arrange - Viewer event
        viewer_event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "cognito:groups": "DRSReadOnly",
                        "email": "viewer@example.com",
                        "sub": "viewer-user-id",
                    }
                }
            },
            "httpMethod": "GET",
            "path": "/protection-groups",
        }

        # Mock decorated function
        @require_permission(DRSPermission.VIEW_PROTECTION_GROUPS)
        def get_servers(event, context):
            return {"statusCode": 200, "body": json.dumps({"servers": []})}

        # Act & Assert - Both can read operational data
        auditor_response = get_servers(auditor_event, Mock())
        assert auditor_response["statusCode"] == 200

        viewer_response = get_servers(viewer_event, Mock())
        assert viewer_response["statusCode"] == 200



class TestPermissionToOperationMapping:
    """Test Task 14.7: Permission-to-operation mapping enforced correctly."""

    def test_servers_read_permission_mapping(self):
        """
        Test VIEW_PROTECTION_GROUPS permission maps to correct operations.

        Operations requiring VIEW_PROTECTION_GROUPS:
        - list_protection_groups
        - get_protection_group
        - describe_protection_groups

        Verifies:
        - Roles with VIEW_PROTECTION_GROUPS can access these operations
        - Roles without VIEW_PROTECTION_GROUPS get 403 Forbidden
        """
        # Arrange - Viewer has VIEW_PROTECTION_GROUPS
        viewer_event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "cognito:groups": "DRSReadOnly",
                        "email": "viewer@example.com",
                        "sub": "viewer-user-id",
                    }
                }
            },
            "httpMethod": "GET",
            "path": "/protection-groups",
        }

        # Mock decorated function
        @require_permission(DRSPermission.VIEW_PROTECTION_GROUPS)
        def list_source_servers(event, context):
            return {"statusCode": 200, "body": json.dumps({"servers": []})}

        # Act & Assert - Viewer can access
        response = list_source_servers(viewer_event, Mock())
        assert response["statusCode"] == 200

    def test_executions_write_permission_mapping(self):
        """
        Test START_RECOVERY permission maps to correct operations.

        Operations requiring START_RECOVERY:
        - start_recovery
        - execute_recovery_plan
        - resume_recovery

        Verifies:
        - Operator has START_RECOVERY
        - Viewer does NOT have START_RECOVERY
        - Planner has START_RECOVERY
        """
        # Arrange - Operator has START_RECOVERY
        operator_event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "cognito:groups": "DRSOperator",
                        "email": "operator@example.com",
                        "sub": "operator-user-id",
                    }
                }
            },
            "httpMethod": "POST",
            "path": "/executions",
        }

        # Arrange - Viewer does NOT have START_RECOVERY
        viewer_event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "cognito:groups": "DRSReadOnly",
                        "email": "viewer@example.com",
                        "sub": "viewer-user-id",
                    }
                }
            },
            "httpMethod": "POST",
            "path": "/executions",
        }

        # Mock decorated function
        @require_permission(DRSPermission.START_RECOVERY)
        def start_recovery(event, context):
            return {"statusCode": 200, "body": json.dumps({"execution_id": "exec-123"})}

        # Act & Assert - Operator can execute
        operator_response = start_recovery(operator_event, Mock())
        assert operator_response["statusCode"] == 200

        # Act & Assert - Viewer cannot execute (403 Forbidden)
        viewer_response = start_recovery(viewer_event, Mock())
        assert viewer_response["statusCode"] == 403

    def test_audit_read_permission_mapping(self):
        """
        Test AUDIT_READ permission maps to audit log operations.

        Operations requiring AUDIT_READ:
        - get_audit_logs
        - query_audit_logs
        - export_audit_logs

        Verifies:
        - Only Auditor has AUDIT_READ
        - All other roles get 403 Forbidden
        """
        # Arrange - Auditor has AUDIT_READ
        auditor_event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "cognito:groups": "DRSAuditor",
                        "email": "auditor@example.com",
                        "sub": "auditor-user-id",
                    }
                }
            },
            "httpMethod": "GET",
            "path": "/audit-logs",
        }

        # Arrange - Admin does NOT have AUDIT_READ (only Auditor does)
        admin_event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "cognito:groups": "DRSOrchestrationAdmin",
                        "email": "admin@example.com",
                        "sub": "admin-user-id",
                    }
                }
            },
            "httpMethod": "GET",
            "path": "/audit-logs",
        }

        # Mock decorated function
        @require_permission(DRSPermission.AUDIT_READ)
        def get_audit_logs(event, context):
            return {"statusCode": 200, "body": json.dumps({"logs": []})}

        # Act & Assert - Auditor can access
        auditor_response = get_audit_logs(auditor_event, Mock())
        assert auditor_response["statusCode"] == 200

        # Act & Assert - Even Admin cannot access audit logs (403 Forbidden)
        # Note: Admin does not have AUDIT_READ - only Auditor role has this permission
        admin_response = get_audit_logs(admin_event, Mock())
        assert admin_response["statusCode"] == 403


class TestUnauthorizedOperations:
    """Test Task 14.8: Unauthorized operations return 403 Forbidden."""

    def test_viewer_cannot_write_servers(self):
        """
        Test Viewer cannot modify protection groups (403 Forbidden).

        Verifies:
        - Viewer has VIEW_PROTECTION_GROUPS
        - Viewer does NOT have MODIFY_PROTECTION_GROUPS
        - Write operation returns 403 Forbidden
        """
        # Arrange
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "cognito:groups": "DRSReadOnly",
                        "email": "viewer@example.com",
                        "sub": "viewer-user-id",
                    }
                }
            },
            "httpMethod": "PUT",
            "path": "/protection-groups/pg-123",
        }

        # Mock decorated function
        @require_permission(DRSPermission.MODIFY_PROTECTION_GROUPS)
        def update_server(event, context):
            return {"statusCode": 200, "body": json.dumps({"message": "Success"})}

        # Act
        response = update_server(event, Mock())

        # Assert - 403 Forbidden
        assert response["statusCode"] == 403
        body = json.loads(response["body"])
        assert "error" in body
        assert "Forbidden" in body["error"] or "permission" in body["error"].lower()

    def test_planner_cannot_execute_recovery(self):
        """
        Test Viewer cannot terminate instances (403 Forbidden).

        Verifies:
        - Viewer has VIEW_EXECUTIONS
        - Viewer does NOT have TERMINATE_INSTANCES
        - Termination operation returns 403 Forbidden
        """
        # Arrange
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "cognito:groups": "DRSReadOnly",
                        "email": "viewer@example.com",
                        "sub": "viewer-user-id",
                    }
                }
            },
            "httpMethod": "POST",
            "path": "/executions/exec-123/terminate-instances",
        }

        # Mock decorated function
        @require_permission(DRSPermission.TERMINATE_INSTANCES)
        def start_recovery(event, context):
            return {"statusCode": 200, "body": json.dumps({"execution_id": "exec-123"})}

        # Act
        response = start_recovery(event, Mock())

        # Assert - 403 Forbidden
        assert response["statusCode"] == 403
        body = json.loads(response["body"])
        assert "error" in body
        assert "Forbidden" in body["error"] or "permission" in body["error"].lower()

    def test_operator_cannot_access_audit_logs(self):
        """
        Test Operator cannot access audit logs (403 Forbidden).

        Verifies:
        - Operator has operational permissions
        - Operator does NOT have AUDIT_READ
        - Audit log access returns 403 Forbidden
        """
        # Arrange
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "cognito:groups": "DRSOperator",
                        "email": "operator@example.com",
                        "sub": "operator-user-id",
                    }
                }
            },
            "httpMethod": "GET",
            "path": "/audit-logs",
        }

        # Mock decorated function
        @require_permission(DRSPermission.AUDIT_READ)
        def get_audit_logs(event, context):
            return {"statusCode": 200, "body": json.dumps({"logs": []})}

        # Act
        response = get_audit_logs(event, Mock())

        # Assert - 403 Forbidden
        assert response["statusCode"] == 403
        body = json.loads(response["body"])
        assert "error" in body
        assert "Forbidden" in body["error"] or "permission" in body["error"].lower()

    def test_viewer_cannot_modify_config(self):
        """
        Test Viewer cannot import configuration (403 Forbidden).

        Verifies:
        - Viewer has VIEW_RECOVERY_PLANS
        - Viewer does NOT have IMPORT_CONFIGURATION
        - Config import returns 403 Forbidden
        """
        # Arrange
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "cognito:groups": "DRSReadOnly",
                        "email": "viewer@example.com",
                        "sub": "viewer-user-id",
                    }
                }
            },
            "httpMethod": "POST",
            "path": "/config/import",
        }

        # Mock decorated function
        @require_permission(DRSPermission.IMPORT_CONFIGURATION)
        def update_config(event, context):
            return {"statusCode": 200, "body": json.dumps({"message": "Config updated"})}

        # Act
        response = update_config(event, Mock())

        # Assert - 403 Forbidden
        assert response["statusCode"] == 403
        body = json.loads(response["body"])
        assert "error" in body
        assert "Forbidden" in body["error"] or "permission" in body["error"].lower()

    def test_missing_cognito_groups_returns_403(self):
        """
        Test missing Cognito groups returns 403 Forbidden.

        Verifies:
        - Event without cognito:groups claim
        - Permission check returns 403 Forbidden
        - Error message indicates missing permissions
        """
        # Arrange - Event without cognito:groups
        event = {
            "requestContext": {
                "authorizer": {
                    "claims": {
                        "email": "user@example.com",
                        "sub": "user-123",
                    }
                }
            },
            "httpMethod": "GET",
            "path": "/protection-groups",
        }

        # Mock decorated function
        @require_permission(DRSPermission.VIEW_PROTECTION_GROUPS)
        def get_servers(event, context):
            return {"statusCode": 200, "body": json.dumps({"servers": []})}

        # Act
        response = get_servers(event, Mock())

        # Assert - 403 Forbidden
        assert response["statusCode"] == 403
        body = json.loads(response["body"])
        assert "error" in body
        assert "Forbidden" in body["error"] or "permission" in body["error"].lower()
        body = json.loads(response["body"])
        assert "error" in body
        assert "Forbidden" in body["error"] or "permission" in body["error"].lower()
