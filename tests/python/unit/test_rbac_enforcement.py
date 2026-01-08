"""
Comprehensive RBAC Enforcement Tests

Tests that ALL API endpoints properly enforce role-based access control.
This ensures that unauthorized users cannot access protected resources.

Test Matrix:
- DRSOrchestrationAdmin: Full access to all endpoints
- DRSRecoveryManager: Full recovery access, no account deletion
- DRSPlanManager: Can manage plans/groups, no instance termination
- DRSOperator: Can execute recovery, no create/delete
- DRSReadOnly: View-only access, no write operations
"""

import json
import os
import sys

import pytest

# Add lambda/shared directory to path for imports
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "lambda", "shared"
    ),
)

from rbac_middleware import (
    ENDPOINT_PERMISSIONS,
    ROLE_PERMISSIONS,
    DRSPermission,
    DRSRole,
    check_authorization,
    get_endpoint_permissions,
    get_user_permissions,
    has_any_permission,
)


def create_event(method: str, path: str, group: str) -> dict:
    """Create a mock API Gateway event with specified role."""
    return {
        "httpMethod": method,
        "path": path,
        "headers": {"authorization": "Bearer test-token"},
        "requestContext": {
            "authorizer": {
                "claims": {
                    "email": f"{group.lower()}@example.com",
                    "sub": f"{group.lower()}-123",
                    "cognito:username": group.lower(),
                    "cognito:groups": group,
                }
            }
        },
    }


class TestEndpointPermissionsCoverage:
    """Verify all critical endpoints have permission mappings."""

    def test_protection_groups_endpoints_have_permissions(self):
        """All protection group endpoints should have permissions defined."""
        endpoints = [
            ("GET", "/protection-groups"),
            ("POST", "/protection-groups"),
            ("POST", "/protection-groups/resolve"),
            ("GET", "/protection-groups/{id}"),
            ("PUT", "/protection-groups/{id}"),
            ("DELETE", "/protection-groups/{id}"),
        ]
        for method, path in endpoints:
            perms = ENDPOINT_PERMISSIONS.get((method, path), None)
            assert perms is not None, f"Missing permissions for {method} {path}"
            assert len(perms) > 0, f"Empty permissions for {method} {path}"

    def test_recovery_plans_endpoints_have_permissions(self):
        """All recovery plan endpoints should have permissions defined."""
        endpoints = [
            ("GET", "/recovery-plans"),
            ("POST", "/recovery-plans"),
            ("GET", "/recovery-plans/{id}"),
            ("PUT", "/recovery-plans/{id}"),
            ("DELETE", "/recovery-plans/{id}"),
            ("POST", "/recovery-plans/{id}/execute"),
            ("GET", "/recovery-plans/{id}/check-existing-instances"),
        ]
        for method, path in endpoints:
            perms = ENDPOINT_PERMISSIONS.get((method, path), None)
            assert perms is not None, f"Missing permissions for {method} {path}"
            assert len(perms) > 0, f"Empty permissions for {method} {path}"

    def test_executions_endpoints_have_permissions(self):
        """All execution endpoints should have permissions defined."""
        endpoints = [
            ("GET", "/executions"),
            ("POST", "/executions"),
            ("DELETE", "/executions"),
            ("POST", "/executions/delete"),
            ("GET", "/executions/{executionId}"),
            ("POST", "/executions/{executionId}/cancel"),
            ("POST", "/executions/{executionId}/pause"),
            ("POST", "/executions/{executionId}/resume"),
            ("POST", "/executions/{executionId}/terminate-instances"),
            ("GET", "/executions/{executionId}/job-logs"),
            ("GET", "/executions/{executionId}/termination-status"),
        ]
        for method, path in endpoints:
            perms = ENDPOINT_PERMISSIONS.get((method, path), None)
            assert perms is not None, f"Missing permissions for {method} {path}"
            assert len(perms) > 0, f"Empty permissions for {method} {path}"

    def test_account_endpoints_have_permissions(self):
        """All account management endpoints should have permissions defined."""
        endpoints = [
            ("GET", "/accounts/targets"),
            ("POST", "/accounts/targets"),
            ("PUT", "/accounts/targets/{id}"),
            ("DELETE", "/accounts/targets/{id}"),
            ("POST", "/accounts/targets/{id}/validate"),
            ("GET", "/accounts/current"),
        ]
        for method, path in endpoints:
            perms = ENDPOINT_PERMISSIONS.get((method, path), None)
            assert perms is not None, f"Missing permissions for {method} {path}"
            assert len(perms) > 0, f"Empty permissions for {method} {path}"

    def test_config_endpoints_have_permissions(self):
        """Configuration endpoints should have permissions defined."""
        endpoints = [
            ("GET", "/config/export"),
            ("POST", "/config/import"),
            ("GET", "/config/tag-sync"),
            ("PUT", "/config/tag-sync"),
        ]
        for method, path in endpoints:
            perms = ENDPOINT_PERMISSIONS.get((method, path), None)
            assert perms is not None, f"Missing permissions for {method} {path}"
            assert len(perms) > 0, f"Empty permissions for {method} {path}"

    def test_drs_endpoints_have_permissions(self):
        """DRS operation endpoints should have permissions defined."""
        endpoints = [
            ("GET", "/drs/source-servers"),
            ("GET", "/drs/quotas"),
            ("POST", "/drs/tag-sync"),
            ("GET", "/drs/accounts"),
        ]
        for method, path in endpoints:
            perms = ENDPOINT_PERMISSIONS.get((method, path), None)
            assert perms is not None, f"Missing permissions for {method} {path}"
            assert len(perms) > 0, f"Empty permissions for {method} {path}"

    def test_ec2_endpoints_have_permissions(self):
        """EC2 resource endpoints should have permissions defined."""
        endpoints = [
            ("GET", "/ec2/subnets"),
            ("GET", "/ec2/security-groups"),
            ("GET", "/ec2/instance-profiles"),
            ("GET", "/ec2/instance-types"),
        ]
        for method, path in endpoints:
            perms = ENDPOINT_PERMISSIONS.get((method, path), None)
            assert perms is not None, f"Missing permissions for {method} {path}"
            assert len(perms) > 0, f"Empty permissions for {method} {path}"

    def test_user_permissions_endpoint_exists(self):
        """User permissions endpoint should exist (empty permissions = all authenticated)."""
        perms = ENDPOINT_PERMISSIONS.get(("GET", "/user/permissions"), None)
        assert perms is not None, "Missing permissions for GET /user/permissions"
        # Empty list means all authenticated users can access
        assert perms == [], "User permissions should be accessible to all authenticated users"


class TestReadOnlyRoleRestrictions:
    """Test that DRSReadOnly role cannot perform write operations."""

    @pytest.mark.parametrize(
        "method,path,description",
        [
            ("POST", "/protection-groups", "create protection group"),
            ("PUT", "/protection-groups/{id}", "update protection group"),
            ("DELETE", "/protection-groups/{id}", "delete protection group"),
            ("POST", "/recovery-plans", "create recovery plan"),
            ("PUT", "/recovery-plans/{id}", "update recovery plan"),
            ("DELETE", "/recovery-plans/{id}", "delete recovery plan"),
            ("POST", "/recovery-plans/{id}/execute", "execute recovery plan"),
            ("POST", "/executions", "start execution"),
            ("POST", "/executions/{executionId}/cancel", "cancel execution"),
            ("POST", "/executions/{executionId}/pause", "pause execution"),
            ("POST", "/executions/{executionId}/resume", "resume execution"),
            (
                "POST",
                "/executions/{executionId}/terminate-instances",
                "terminate instances",
            ),
            ("POST", "/accounts/targets", "register account"),
            ("PUT", "/accounts/targets/{id}", "modify account"),
            ("DELETE", "/accounts/targets/{id}", "delete account"),
            ("GET", "/config/export", "export configuration"),
            ("POST", "/config/import", "import configuration"),
        ],
    )
    def test_read_only_cannot_perform_write_operation(
        self, method, path, description
    ):
        """DRSReadOnly should be denied access to write operations."""
        event = create_event(method, path, "DRSReadOnly")
        result = check_authorization(event)

        # Get required permissions for this endpoint
        required_perms = get_endpoint_permissions(method, path)

        if required_perms:
            # If permissions are defined, read-only should NOT have them
            user = {"groups": ["DRSReadOnly"]}
            has_access = has_any_permission(user, required_perms)
            assert (
                has_access is False
            ), f"DRSReadOnly should NOT be able to {description}"

    @pytest.mark.parametrize(
        "method,path,description",
        [
            ("GET", "/protection-groups", "view protection groups"),
            ("GET", "/protection-groups/{id}", "view protection group"),
            ("GET", "/recovery-plans", "view recovery plans"),
            ("GET", "/recovery-plans/{id}", "view recovery plan"),
            ("GET", "/executions", "view executions"),
            ("GET", "/executions/{executionId}", "view execution"),
            ("GET", "/accounts/targets", "view accounts"),
        ],
    )
    def test_read_only_can_view_resources(self, method, path, description):
        """DRSReadOnly should be able to view resources."""
        event = create_event(method, path, "DRSReadOnly")
        result = check_authorization(event)

        # Get required permissions for this endpoint
        required_perms = get_endpoint_permissions(method, path)

        if required_perms:
            user = {"groups": ["DRSReadOnly"]}
            has_access = has_any_permission(user, required_perms)
            assert has_access is True, f"DRSReadOnly should be able to {description}"


class TestOperatorRoleRestrictions:
    """Test that DRSOperator role has appropriate restrictions."""

    @pytest.mark.parametrize(
        "method,path,description",
        [
            ("POST", "/protection-groups", "create protection group"),
            ("DELETE", "/protection-groups/{id}", "delete protection group"),
            ("POST", "/recovery-plans", "create recovery plan"),
            ("DELETE", "/recovery-plans/{id}", "delete recovery plan"),
            (
                "POST",
                "/executions/{executionId}/terminate-instances",
                "terminate instances",
            ),
            ("POST", "/accounts/targets", "register account"),
            ("DELETE", "/accounts/targets/{id}", "delete account"),
            ("GET", "/config/export", "export configuration"),
            ("POST", "/config/import", "import configuration"),
        ],
    )
    def test_operator_cannot_perform_restricted_operations(
        self, method, path, description
    ):
        """DRSOperator should be denied access to restricted operations."""
        required_perms = get_endpoint_permissions(method, path)

        if required_perms:
            user = {"groups": ["DRSOperator"]}
            has_access = has_any_permission(user, required_perms)
            assert (
                has_access is False
            ), f"DRSOperator should NOT be able to {description}"

    @pytest.mark.parametrize(
        "method,path,description",
        [
            ("GET", "/protection-groups", "view protection groups"),
            ("PUT", "/protection-groups/{id}", "modify protection group"),
            ("GET", "/recovery-plans", "view recovery plans"),
            ("PUT", "/recovery-plans/{id}", "modify recovery plan"),
            ("POST", "/recovery-plans/{id}/execute", "execute recovery plan"),
            ("GET", "/executions", "view executions"),
            ("POST", "/executions", "start execution"),
            ("POST", "/executions/{executionId}/cancel", "cancel execution"),
            ("POST", "/executions/{executionId}/pause", "pause execution"),
            ("POST", "/executions/{executionId}/resume", "resume execution"),
        ],
    )
    def test_operator_can_perform_allowed_operations(
        self, method, path, description
    ):
        """DRSOperator should be able to perform allowed operations."""
        required_perms = get_endpoint_permissions(method, path)

        if required_perms:
            user = {"groups": ["DRSOperator"]}
            has_access = has_any_permission(user, required_perms)
            assert has_access is True, f"DRSOperator should be able to {description}"


class TestPlanManagerRoleRestrictions:
    """Test that DRSPlanManager role has appropriate restrictions."""

    @pytest.mark.parametrize(
        "method,path,description",
        [
            (
                "POST",
                "/executions/{executionId}/terminate-instances",
                "terminate instances",
            ),
            ("POST", "/accounts/targets", "register account"),
            ("DELETE", "/accounts/targets/{id}", "delete account"),
            ("PUT", "/accounts/targets/{id}", "modify account"),
            ("GET", "/config/export", "export configuration"),
            ("POST", "/config/import", "import configuration"),
        ],
    )
    def test_plan_manager_cannot_perform_restricted_operations(
        self, method, path, description
    ):
        """DRSPlanManager should be denied access to restricted operations."""
        required_perms = get_endpoint_permissions(method, path)

        if required_perms:
            user = {"groups": ["DRSPlanManager"]}
            has_access = has_any_permission(user, required_perms)
            assert (
                has_access is False
            ), f"DRSPlanManager should NOT be able to {description}"

    @pytest.mark.parametrize(
        "method,path,description",
        [
            ("POST", "/protection-groups", "create protection group"),
            ("PUT", "/protection-groups/{id}", "modify protection group"),
            ("DELETE", "/protection-groups/{id}", "delete protection group"),
            ("POST", "/recovery-plans", "create recovery plan"),
            ("PUT", "/recovery-plans/{id}", "modify recovery plan"),
            ("DELETE", "/recovery-plans/{id}", "delete recovery plan"),
            ("POST", "/recovery-plans/{id}/execute", "execute recovery plan"),
            ("POST", "/executions", "start execution"),
        ],
    )
    def test_plan_manager_can_perform_allowed_operations(
        self, method, path, description
    ):
        """DRSPlanManager should be able to perform allowed operations."""
        required_perms = get_endpoint_permissions(method, path)

        if required_perms:
            user = {"groups": ["DRSPlanManager"]}
            has_access = has_any_permission(user, required_perms)
            assert (
                has_access is True
            ), f"DRSPlanManager should be able to {description}"


class TestRecoveryManagerRoleRestrictions:
    """Test that DRSRecoveryManager role has appropriate restrictions."""

    @pytest.mark.parametrize(
        "method,path,description",
        [
            ("DELETE", "/accounts/targets/{id}", "delete account"),
        ],
    )
    def test_recovery_manager_cannot_delete_accounts(
        self, method, path, description
    ):
        """DRSRecoveryManager should not be able to delete accounts."""
        required_perms = get_endpoint_permissions(method, path)

        if required_perms:
            user = {"groups": ["DRSRecoveryManager"]}
            has_access = has_any_permission(user, required_perms)
            assert (
                has_access is False
            ), f"DRSRecoveryManager should NOT be able to {description}"

    @pytest.mark.parametrize(
        "method,path,description",
        [
            ("POST", "/protection-groups", "create protection group"),
            ("DELETE", "/protection-groups/{id}", "delete protection group"),
            ("POST", "/recovery-plans", "create recovery plan"),
            ("DELETE", "/recovery-plans/{id}", "delete recovery plan"),
            (
                "POST",
                "/executions/{executionId}/terminate-instances",
                "terminate instances",
            ),
            ("POST", "/accounts/targets", "register account"),
            ("PUT", "/accounts/targets/{id}", "modify account"),
            ("GET", "/config/export", "export configuration"),
            ("POST", "/config/import", "import configuration"),
        ],
    )
    def test_recovery_manager_can_perform_most_operations(
        self, method, path, description
    ):
        """DRSRecoveryManager should be able to perform most operations."""
        required_perms = get_endpoint_permissions(method, path)

        if required_perms:
            user = {"groups": ["DRSRecoveryManager"]}
            has_access = has_any_permission(user, required_perms)
            assert (
                has_access is True
            ), f"DRSRecoveryManager should be able to {description}"


class TestAdminRoleFullAccess:
    """Test that DRSOrchestrationAdmin has full access."""

    @pytest.mark.parametrize(
        "method,path",
        [
            ("GET", "/protection-groups"),
            ("POST", "/protection-groups"),
            ("GET", "/protection-groups/{id}"),
            ("PUT", "/protection-groups/{id}"),
            ("DELETE", "/protection-groups/{id}"),
            ("GET", "/recovery-plans"),
            ("POST", "/recovery-plans"),
            ("GET", "/recovery-plans/{id}"),
            ("PUT", "/recovery-plans/{id}"),
            ("DELETE", "/recovery-plans/{id}"),
            ("POST", "/recovery-plans/{id}/execute"),
            ("GET", "/executions"),
            ("POST", "/executions"),
            ("GET", "/executions/{executionId}"),
            ("POST", "/executions/{executionId}/cancel"),
            ("POST", "/executions/{executionId}/pause"),
            ("POST", "/executions/{executionId}/resume"),
            ("POST", "/executions/{executionId}/terminate-instances"),
            ("GET", "/accounts/targets"),
            ("POST", "/accounts/targets"),
            ("PUT", "/accounts/targets/{id}"),
            ("DELETE", "/accounts/targets/{id}"),
            ("GET", "/config/export"),
            ("POST", "/config/import"),
        ],
    )
    def test_admin_has_access_to_all_endpoints(self, method, path):
        """DRSOrchestrationAdmin should have access to all endpoints."""
        required_perms = get_endpoint_permissions(method, path)

        if required_perms:
            user = {"groups": ["DRSOrchestrationAdmin"]}
            has_access = has_any_permission(user, required_perms)
            assert (
                has_access is True
            ), f"DRSOrchestrationAdmin should have access to {method} {path}"


class TestTerminateInstancesRestriction:
    """Test that terminate-instances is properly restricted."""

    def test_only_admin_and_recovery_manager_can_terminate(self):
        """Only Admin and RecoveryManager should be able to terminate instances."""
        required_perms = get_endpoint_permissions(
            "POST", "/executions/{executionId}/terminate-instances"
        )

        # These roles SHOULD be able to terminate
        for role in ["DRSOrchestrationAdmin", "DRSRecoveryManager"]:
            user = {"groups": [role]}
            has_access = has_any_permission(user, required_perms)
            assert has_access is True, f"{role} should be able to terminate instances"

        # These roles should NOT be able to terminate
        for role in ["DRSPlanManager", "DRSOperator", "DRSReadOnly"]:
            user = {"groups": [role]}
            has_access = has_any_permission(user, required_perms)
            assert (
                has_access is False
            ), f"{role} should NOT be able to terminate instances"


class TestAccountDeletionRestriction:
    """Test that account deletion is properly restricted."""

    def test_only_admin_can_delete_accounts(self):
        """Only Admin should be able to delete accounts."""
        # Use raw ENDPOINT_PERMISSIONS to avoid path normalization issues
        perms = ENDPOINT_PERMISSIONS.get(("DELETE", "/accounts/targets/{id}"))
        assert perms is not None, "Delete account endpoint must have permissions"
        
        # Only admin SHOULD be able to delete accounts
        user = {"groups": ["DRSOrchestrationAdmin"]}
        has_access = has_any_permission(user, perms)
        assert has_access is True, "Admin should be able to delete accounts"

        # These roles should NOT be able to delete accounts
        for role in [
            "DRSRecoveryManager",
            "DRSPlanManager",
            "DRSOperator",
            "DRSReadOnly",
        ]:
            user = {"groups": [role]}
            has_access = has_any_permission(user, perms)
            assert (
                has_access is False
            ), f"{role} should NOT be able to delete accounts"


class TestConfigurationManagementRestriction:
    """Test that configuration import/export is properly restricted."""

    def test_only_admin_and_recovery_manager_can_export_config(self):
        """Only Admin and RecoveryManager should be able to export config."""
        # Use raw ENDPOINT_PERMISSIONS to avoid path normalization issues
        perms = ENDPOINT_PERMISSIONS.get(("GET", "/config/export"))
        assert perms is not None, "Export config endpoint must have permissions"

        # These roles SHOULD be able to export
        for role in ["DRSOrchestrationAdmin", "DRSRecoveryManager"]:
            user = {"groups": [role]}
            has_access = has_any_permission(user, perms)
            assert has_access is True, f"{role} should be able to export config"

        # These roles should NOT be able to export
        for role in ["DRSPlanManager", "DRSOperator", "DRSReadOnly"]:
            user = {"groups": [role]}
            has_access = has_any_permission(user, perms)
            assert has_access is False, f"{role} should NOT be able to export config"

    def test_only_admin_and_recovery_manager_can_import_config(self):
        """Only Admin and RecoveryManager should be able to import config."""
        # Use raw ENDPOINT_PERMISSIONS to avoid path normalization issues
        perms = ENDPOINT_PERMISSIONS.get(("POST", "/config/import"))
        assert perms is not None, "Import config endpoint must have permissions"

        # These roles SHOULD be able to import
        for role in ["DRSOrchestrationAdmin", "DRSRecoveryManager"]:
            user = {"groups": [role]}
            has_access = has_any_permission(user, perms)
            assert has_access is True, f"{role} should be able to import config"

        # These roles should NOT be able to import
        for role in ["DRSPlanManager", "DRSOperator", "DRSReadOnly"]:
            user = {"groups": [role]}
            has_access = has_any_permission(user, perms)
            assert has_access is False, f"{role} should NOT be able to import config"


class TestNoAuthenticatedUserBypass:
    """Test that unauthenticated users cannot bypass RBAC."""

    def test_empty_groups_has_no_permissions(self):
        """User with no groups should have no permissions."""
        user = {"groups": []}
        permissions = get_user_permissions(user)
        assert len(permissions) == 0, "User with no groups should have no permissions"

    def test_unknown_group_has_no_permissions(self):
        """User with unknown group should have no permissions."""
        user = {"groups": ["UnknownGroup", "FakeAdmin"]}
        permissions = get_user_permissions(user)
        assert (
            len(permissions) == 0
        ), "User with unknown groups should have no permissions"

    def test_missing_groups_key_has_no_permissions(self):
        """User without groups key should have no permissions."""
        user = {}
        permissions = get_user_permissions(user)
        assert (
            len(permissions) == 0
        ), "User without groups key should have no permissions"


class TestRoleHierarchy:
    """Test that role permissions follow expected hierarchy."""

    def test_admin_has_more_permissions_than_recovery_manager(self):
        """Admin should have >= permissions than RecoveryManager."""
        admin_perms = set(ROLE_PERMISSIONS[DRSRole.DRS_ORCHESTRATION_ADMIN])
        recovery_manager_perms = set(ROLE_PERMISSIONS[DRSRole.DRS_RECOVERY_MANAGER])

        # Admin should have all recovery manager permissions
        assert recovery_manager_perms.issubset(
            admin_perms
        ), "Admin should have all RecoveryManager permissions"

    def test_recovery_manager_has_more_permissions_than_plan_manager(self):
        """RecoveryManager should have >= permissions than PlanManager."""
        recovery_manager_perms = set(ROLE_PERMISSIONS[DRSRole.DRS_RECOVERY_MANAGER])
        plan_manager_perms = set(ROLE_PERMISSIONS[DRSRole.DRS_PLAN_MANAGER])

        # Recovery manager should have all plan manager permissions
        assert plan_manager_perms.issubset(
            recovery_manager_perms
        ), "RecoveryManager should have all PlanManager permissions"

    def test_plan_manager_has_more_permissions_than_operator(self):
        """PlanManager should have >= permissions than Operator."""
        plan_manager_perms = set(ROLE_PERMISSIONS[DRSRole.DRS_PLAN_MANAGER])
        operator_perms = set(ROLE_PERMISSIONS[DRSRole.DRS_OPERATOR])

        # Plan manager should have all operator permissions
        assert operator_perms.issubset(
            plan_manager_perms
        ), "PlanManager should have all Operator permissions"

    def test_operator_has_more_permissions_than_read_only(self):
        """Operator should have >= permissions than ReadOnly."""
        operator_perms = set(ROLE_PERMISSIONS[DRSRole.DRS_OPERATOR])
        read_only_perms = set(ROLE_PERMISSIONS[DRSRole.DRS_READ_ONLY])

        # Operator should have all read-only permissions
        assert read_only_perms.issubset(
            operator_perms
        ), "Operator should have all ReadOnly permissions"


class TestCriticalSecurityEndpoints:
    """Test critical security-sensitive endpoints."""

    def test_terminate_instances_requires_terminate_permission(self):
        """Terminate instances endpoint must require TERMINATE_INSTANCES permission."""
        perms = ENDPOINT_PERMISSIONS.get(
            ("POST", "/executions/{executionId}/terminate-instances")
        )
        assert perms is not None, "Terminate instances endpoint must have permissions"
        assert (
            DRSPermission.TERMINATE_INSTANCES in perms
        ), "Terminate instances must require TERMINATE_INSTANCES permission"

    def test_delete_account_requires_delete_permission(self):
        """Delete account endpoint must require DELETE_ACCOUNTS permission."""
        perms = ENDPOINT_PERMISSIONS.get(("DELETE", "/accounts/targets/{id}"))
        assert perms is not None, "Delete account endpoint must have permissions"
        assert (
            DRSPermission.DELETE_ACCOUNTS in perms
        ), "Delete account must require DELETE_ACCOUNTS permission"

    def test_import_config_requires_import_permission(self):
        """Import config endpoint must require IMPORT_CONFIGURATION permission."""
        perms = ENDPOINT_PERMISSIONS.get(("POST", "/config/import"))
        assert perms is not None, "Import config endpoint must have permissions"
        assert (
            DRSPermission.IMPORT_CONFIGURATION in perms
        ), "Import config must require IMPORT_CONFIGURATION permission"


class TestGetEndpointPermissionsFixed:
    """
    Test that get_endpoint_permissions correctly normalizes paths.
    
    These tests verify the fix for the path normalization bug where
    static segments like 'accounts', 'targets', 'config' were incorrectly
    being replaced with {id}.
    """

    def test_accounts_targets_path_normalization_fixed(self):
        """
        get_endpoint_permissions should correctly normalize /accounts/targets/{id}.
        """
        # Raw permissions should exist
        raw_perms = ENDPOINT_PERMISSIONS.get(("DELETE", "/accounts/targets/{id}"))
        assert raw_perms is not None, "Raw permissions should exist"
        assert len(raw_perms) > 0, "Raw permissions should not be empty"
        
        # Normalized permissions should now work correctly
        normalized_perms = get_endpoint_permissions("DELETE", "/accounts/targets/acc-123")
        assert len(normalized_perms) > 0, "Normalized permissions should not be empty after fix"
        assert normalized_perms == raw_perms, "Normalized should match raw permissions"

    def test_config_export_path_normalization_fixed(self):
        """
        get_endpoint_permissions should correctly handle /config/export.
        """
        raw_perms = ENDPOINT_PERMISSIONS.get(("GET", "/config/export"))
        assert raw_perms is not None, "Raw permissions should exist"
        
        normalized_perms = get_endpoint_permissions("GET", "/config/export")
        assert len(normalized_perms) > 0, "Normalized permissions should not be empty"
        assert normalized_perms == raw_perms, "Normalized should match raw permissions"

    def test_config_import_path_normalization_fixed(self):
        """
        get_endpoint_permissions should correctly handle /config/import.
        """
        raw_perms = ENDPOINT_PERMISSIONS.get(("POST", "/config/import"))
        assert raw_perms is not None, "Raw permissions should exist"
        
        normalized_perms = get_endpoint_permissions("POST", "/config/import")
        assert len(normalized_perms) > 0, "Normalized permissions should not be empty"
        assert normalized_perms == raw_perms, "Normalized should match raw permissions"

    def test_protection_groups_path_not_normalized(self):
        """
        /protection-groups should NOT be normalized to /{id}.
        """
        perms = get_endpoint_permissions("GET", "/protection-groups")
        assert len(perms) > 0, "/protection-groups should have permissions"
        
        raw_perms = ENDPOINT_PERMISSIONS.get(("GET", "/protection-groups"))
        assert perms == raw_perms, "Should match raw permissions"

    def test_protection_groups_with_id_normalized(self):
        """
        /protection-groups/{uuid} should be normalized to /protection-groups/{id}.
        """
        perms = get_endpoint_permissions("GET", "/protection-groups/pg-abc123def456")
        assert len(perms) > 0, "/protection-groups/{id} should have permissions"
        
        raw_perms = ENDPOINT_PERMISSIONS.get(("GET", "/protection-groups/{id}"))
        assert perms == raw_perms, "Should match raw permissions for {id}"

    def test_executions_with_uuid_normalized(self):
        """
        /executions/{uuid} should be normalized to /executions/{executionId}.
        """
        perms = get_endpoint_permissions("GET", "/executions/exec-abc123-def456-789")
        assert len(perms) > 0, "/executions/{executionId} should have permissions"
        
        raw_perms = ENDPOINT_PERMISSIONS.get(("GET", "/executions/{executionId}"))
        assert perms == raw_perms, "Should match raw permissions for {executionId}"

    def test_executions_cancel_normalized(self):
        """
        /executions/{uuid}/cancel should be normalized correctly.
        """
        perms = get_endpoint_permissions("POST", "/executions/exec-abc123/cancel")
        assert len(perms) > 0, "/executions/{executionId}/cancel should have permissions"
        
        raw_perms = ENDPOINT_PERMISSIONS.get(("POST", "/executions/{executionId}/cancel"))
        assert perms == raw_perms, "Should match raw permissions"

    def test_drs_source_servers_not_normalized(self):
        """
        /drs/source-servers should NOT be normalized.
        """
        perms = get_endpoint_permissions("GET", "/drs/source-servers")
        assert len(perms) > 0, "/drs/source-servers should have permissions"
        
        raw_perms = ENDPOINT_PERMISSIONS.get(("GET", "/drs/source-servers"))
        assert perms == raw_perms, "Should match raw permissions"

    def test_ec2_subnets_not_normalized(self):
        """
        /ec2/subnets should NOT be normalized.
        """
        perms = get_endpoint_permissions("GET", "/ec2/subnets")
        assert len(perms) > 0, "/ec2/subnets should have permissions"
        
        raw_perms = ENDPOINT_PERMISSIONS.get(("GET", "/ec2/subnets"))
        assert perms == raw_perms, "Should match raw permissions"

    def test_accounts_current_not_normalized(self):
        """
        /accounts/current should NOT be normalized.
        """
        perms = get_endpoint_permissions("GET", "/accounts/current")
        assert len(perms) > 0, "/accounts/current should have permissions"
        
        raw_perms = ENDPOINT_PERMISSIONS.get(("GET", "/accounts/current"))
        assert perms == raw_perms, "Should match raw permissions"

    def test_config_tag_sync_not_normalized(self):
        """
        /config/tag-sync should NOT be normalized.
        """
        perms = get_endpoint_permissions("GET", "/config/tag-sync")
        assert len(perms) > 0, "/config/tag-sync should have permissions"
        
        raw_perms = ENDPOINT_PERMISSIONS.get(("GET", "/config/tag-sync"))
        assert perms == raw_perms, "Should match raw permissions"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
