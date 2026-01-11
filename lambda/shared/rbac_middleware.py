"""
RBAC Middleware for AWS DRS Orchestration
Implements role-based access control using Cognito Groups
"""

import json
from enum import Enum
from functools import wraps
from typing import Callable, Dict, List


class DRSRole(Enum):
    """
    DRS Orchestration Role definitions for disaster recovery operations

    Inspired by AWS DRS service roles but designed for orchestration platform
    users:
    - DRSOrchestrationAdmin: Full administrative access (like service
      administrators)
    - DRSRecoveryManager: Can execute and manage recovery operations (like
      recovery coordinators)
    - DRSPlanManager: Can create and modify recovery plans (like DR planners)
    - DRSOperator: Can execute recovery but not modify plans (like on-call
      operators)
    - DRSReadOnly: View-only access for auditing and monitoring (like
      compliance officers)
    """

    # DRS Orchestration Roles (intuitive for disaster recovery teams)
    DRS_ORCHESTRATION_ADMIN = "DRSOrchestrationAdmin"
    DRS_RECOVERY_MANAGER = "DRSRecoveryManager"
    DRS_PLAN_MANAGER = "DRSPlanManager"
    DRS_OPERATOR = "DRSOperator"
    DRS_READ_ONLY = "DRSReadOnly"

    # Legacy AWS-style aliases for security test compatibility
    AWS_ADMIN = "aws:admin"
    AWS_ADMIN_LIMITED = "aws:admin-limited"
    AWS_POWER_USER = "aws:power-user"
    AWS_OPERATOR = "aws:operator"
    AWS_READ_ONLY = "aws:read-only"


class DRSPermission(Enum):
    """DRS Permission definitions for actual DRS business functionality"""

    # Account Management
    REGISTER_ACCOUNTS = "register_accounts"
    DELETE_ACCOUNTS = "delete_accounts"
    MODIFY_ACCOUNTS = "modify_accounts"
    VIEW_ACCOUNTS = "view_accounts"

    # Recovery Operations
    START_RECOVERY = "start_recovery"
    STOP_RECOVERY = "stop_recovery"
    TERMINATE_INSTANCES = "terminate_instances"
    VIEW_EXECUTIONS = "view_executions"

    # Protection Groups
    CREATE_PROTECTION_GROUPS = "create_protection_groups"
    DELETE_PROTECTION_GROUPS = "delete_protection_groups"
    MODIFY_PROTECTION_GROUPS = "modify_protection_groups"
    VIEW_PROTECTION_GROUPS = "view_protection_groups"

    # Recovery Plans
    CREATE_RECOVERY_PLANS = "create_recovery_plans"
    DELETE_RECOVERY_PLANS = "delete_recovery_plans"
    MODIFY_RECOVERY_PLANS = "modify_recovery_plans"
    VIEW_RECOVERY_PLANS = "view_recovery_plans"

    # Configuration Management
    EXPORT_CONFIGURATION = "export_configuration"
    IMPORT_CONFIGURATION = "import_configuration"


# Role-Permission Matrix (focused on DRS orchestration business functionality)
ROLE_PERMISSIONS = {
    # DRSOrchestrationAdmin - Full administrative access (like AWS service
    # administrators)
    DRSRole.DRS_ORCHESTRATION_ADMIN: [
        # Account Management - Full access
        DRSPermission.REGISTER_ACCOUNTS,
        DRSPermission.DELETE_ACCOUNTS,
        DRSPermission.MODIFY_ACCOUNTS,
        DRSPermission.VIEW_ACCOUNTS,
        # Recovery Operations - Full access
        DRSPermission.START_RECOVERY,
        DRSPermission.STOP_RECOVERY,
        DRSPermission.TERMINATE_INSTANCES,
        DRSPermission.VIEW_EXECUTIONS,
        # Protection Groups - Full access
        DRSPermission.CREATE_PROTECTION_GROUPS,
        DRSPermission.DELETE_PROTECTION_GROUPS,
        DRSPermission.MODIFY_PROTECTION_GROUPS,
        DRSPermission.VIEW_PROTECTION_GROUPS,
        # Recovery Plans - Full access
        DRSPermission.CREATE_RECOVERY_PLANS,
        DRSPermission.DELETE_RECOVERY_PLANS,
        DRSPermission.MODIFY_RECOVERY_PLANS,
        DRSPermission.VIEW_RECOVERY_PLANS,
        # Configuration Management - Full access
        DRSPermission.EXPORT_CONFIGURATION,
        DRSPermission.IMPORT_CONFIGURATION,
    ],
    # DRSRecoveryManager - Can execute and manage all recovery operations
    # (like recovery coordinators)
    DRSRole.DRS_RECOVERY_MANAGER: [
        # Account Management - Can register and modify, but not delete accounts
        DRSPermission.REGISTER_ACCOUNTS,
        DRSPermission.MODIFY_ACCOUNTS,
        DRSPermission.VIEW_ACCOUNTS,
        # Recovery Operations - Full recovery access
        DRSPermission.START_RECOVERY,
        DRSPermission.STOP_RECOVERY,
        DRSPermission.TERMINATE_INSTANCES,
        DRSPermission.VIEW_EXECUTIONS,
        # Protection Groups - Full access
        DRSPermission.CREATE_PROTECTION_GROUPS,
        DRSPermission.DELETE_PROTECTION_GROUPS,
        DRSPermission.MODIFY_PROTECTION_GROUPS,
        DRSPermission.VIEW_PROTECTION_GROUPS,
        # Recovery Plans - Full access
        DRSPermission.CREATE_RECOVERY_PLANS,
        DRSPermission.DELETE_RECOVERY_PLANS,
        DRSPermission.MODIFY_RECOVERY_PLANS,
        DRSPermission.VIEW_RECOVERY_PLANS,
        # Configuration Management - Full access
        DRSPermission.EXPORT_CONFIGURATION,
        DRSPermission.IMPORT_CONFIGURATION,
    ],
    # DRSPlanManager - Can create and modify recovery plans (like DR planners)
    DRSRole.DRS_PLAN_MANAGER: [
        # Account Management - View only
        DRSPermission.VIEW_ACCOUNTS,
        # Recovery Operations - Can start/stop but not terminate instances
        DRSPermission.START_RECOVERY,
        DRSPermission.STOP_RECOVERY,
        DRSPermission.VIEW_EXECUTIONS,
        # Protection Groups - Full access
        DRSPermission.CREATE_PROTECTION_GROUPS,
        DRSPermission.DELETE_PROTECTION_GROUPS,
        DRSPermission.MODIFY_PROTECTION_GROUPS,
        DRSPermission.VIEW_PROTECTION_GROUPS,
        # Recovery Plans - Full access
        DRSPermission.CREATE_RECOVERY_PLANS,
        DRSPermission.DELETE_RECOVERY_PLANS,
        DRSPermission.MODIFY_RECOVERY_PLANS,
        DRSPermission.VIEW_RECOVERY_PLANS,
    ],
    # DRSOperator - Can execute recovery operations but not modify plans
    # (like on-call operators)
    DRSRole.DRS_OPERATOR: [
        # Account Management - View only
        DRSPermission.VIEW_ACCOUNTS,
        # Recovery Operations - Can execute but not terminate instances
        DRSPermission.START_RECOVERY,
        DRSPermission.STOP_RECOVERY,
        DRSPermission.VIEW_EXECUTIONS,
        # Protection Groups - View and modify existing, but not create/delete
        DRSPermission.MODIFY_PROTECTION_GROUPS,
        DRSPermission.VIEW_PROTECTION_GROUPS,
        # Recovery Plans - View and modify existing, but not create/delete
        DRSPermission.MODIFY_RECOVERY_PLANS,
        DRSPermission.VIEW_RECOVERY_PLANS,
    ],
    # DRSReadOnly - View-only access (like compliance officers and auditors)
    DRSRole.DRS_READ_ONLY: [
        # Account Management - View only
        DRSPermission.VIEW_ACCOUNTS,
        # Recovery Operations - View only
        DRSPermission.VIEW_EXECUTIONS,
        # Protection Groups - View only
        DRSPermission.VIEW_PROTECTION_GROUPS,
        # Recovery Plans - View only
        DRSPermission.VIEW_RECOVERY_PLANS,
    ],
}

# API Endpoint to Permission Mapping - TIGHT SECURITY
# ALL endpoints require specific permissions for proper access control
ENDPOINT_PERMISSIONS = {
    # Protection Groups - All operations require permissions
    ("GET", "/protection-groups"): [DRSPermission.VIEW_PROTECTION_GROUPS],
    ("POST", "/protection-groups"): [DRSPermission.CREATE_PROTECTION_GROUPS],
    ("POST", "/protection-groups/resolve"): [DRSPermission.VIEW_PROTECTION_GROUPS],
    ("GET", "/protection-groups/{id}"): [DRSPermission.VIEW_PROTECTION_GROUPS],
    ("PUT", "/protection-groups/{id}"): [DRSPermission.MODIFY_PROTECTION_GROUPS],
    ("DELETE", "/protection-groups/{id}"): [DRSPermission.DELETE_PROTECTION_GROUPS],
    ("POST", "/protection-groups/{id}"): [DRSPermission.MODIFY_PROTECTION_GROUPS],
    
    # Recovery Plans - All operations require permissions
    ("GET", "/recovery-plans"): [DRSPermission.VIEW_RECOVERY_PLANS],
    ("POST", "/recovery-plans"): [DRSPermission.CREATE_RECOVERY_PLANS],
    ("GET", "/recovery-plans/{id}"): [DRSPermission.VIEW_RECOVERY_PLANS],
    ("PUT", "/recovery-plans/{id}"): [DRSPermission.MODIFY_RECOVERY_PLANS],
    ("DELETE", "/recovery-plans/{id}"): [DRSPermission.DELETE_RECOVERY_PLANS],
    ("POST", "/recovery-plans/{id}/execute"): [DRSPermission.START_RECOVERY],
    ("GET", "/recovery-plans/{id}/check-existing-instances"): [DRSPermission.VIEW_RECOVERY_PLANS],
    
    # Executions - All operations require permissions
    ("GET", "/executions"): [DRSPermission.VIEW_EXECUTIONS],
    ("POST", "/executions"): [DRSPermission.START_RECOVERY],
    ("DELETE", "/executions"): [DRSPermission.STOP_RECOVERY],
    ("POST", "/executions/delete"): [DRSPermission.STOP_RECOVERY],
    ("GET", "/executions/{executionId}"): [DRSPermission.VIEW_EXECUTIONS],
    ("POST", "/executions/{executionId}/cancel"): [DRSPermission.STOP_RECOVERY],
    ("POST", "/executions/{executionId}/pause"): [DRSPermission.STOP_RECOVERY],
    ("POST", "/executions/{executionId}/resume"): [DRSPermission.START_RECOVERY],
    ("POST", "/executions/{executionId}/terminate-instances"): [DRSPermission.TERMINATE_INSTANCES],
    ("GET", "/executions/{executionId}/job-logs"): [DRSPermission.VIEW_EXECUTIONS],
    ("GET", "/executions/{executionId}/termination-status"): [DRSPermission.VIEW_EXECUTIONS],
    ("GET", "/executions/{executionId}/recovery-instances"): [DRSPermission.VIEW_EXECUTIONS],
    
    # Account Management - All operations require permissions
    ("GET", "/accounts/targets"): [DRSPermission.VIEW_ACCOUNTS],
    ("POST", "/accounts/targets"): [DRSPermission.REGISTER_ACCOUNTS],
    ("GET", "/accounts/targets/{id}"): [DRSPermission.VIEW_ACCOUNTS],
    ("PUT", "/accounts/targets/{id}"): [DRSPermission.MODIFY_ACCOUNTS],
    ("DELETE", "/accounts/targets/{id}"): [DRSPermission.DELETE_ACCOUNTS],
    ("POST", "/accounts/targets/{id}/validate"): [DRSPermission.VIEW_ACCOUNTS],
    ("GET", "/accounts/current"): [DRSPermission.VIEW_ACCOUNTS],
    
    # Configuration Management - All operations require permissions
    ("GET", "/config/export"): [DRSPermission.EXPORT_CONFIGURATION],
    ("POST", "/config/import"): [DRSPermission.IMPORT_CONFIGURATION],
    ("PUT", "/config/tag-sync"): [DRSPermission.MODIFY_PROTECTION_GROUPS],
    ("GET", "/config/tag-sync"): [DRSPermission.VIEW_PROTECTION_GROUPS],
    
    # DRS Operations - All operations require permissions
    ("GET", "/drs/source-servers"): [DRSPermission.VIEW_PROTECTION_GROUPS],
    ("POST", "/drs/tag-sync"): [DRSPermission.MODIFY_PROTECTION_GROUPS],
    ("GET", "/drs/service-limits"): [DRSPermission.VIEW_PROTECTION_GROUPS],
    
    # EC2 Operations - All operations require permissions
    ("GET", "/ec2/subnets"): [DRSPermission.VIEW_ACCOUNTS],
    ("GET", "/ec2/security-groups"): [DRSPermission.VIEW_ACCOUNTS],
    ("GET", "/ec2/instance-types"): [DRSPermission.VIEW_ACCOUNTS],
    
    # User Management - All operations require permissions
    ("GET", "/user/permissions"): [DRSPermission.VIEW_ACCOUNTS],  # Users can view their own permissions
}


def get_user_from_event(event: Dict) -> Dict:
    """Extract user information from API Gateway event"""
    try:
        authorizer = event.get("requestContext", {}).get("authorizer", {})
        claims = authorizer.get("claims", {})

        # Extract groups from cognito:groups claim
        groups_claim = claims.get("cognito:groups", "")
        if isinstance(groups_claim, list):
            # Already a list
            groups = [group.strip() for group in groups_claim]
        elif isinstance(groups_claim, str):
            # String - could be single group or comma-separated
            groups = (
                [group.strip() for group in groups_claim.split(",")]
                if groups_claim
                else []
            )
        else:
            groups = []

        return {
            "email": claims.get("email", "unknown"),
            "userId": claims.get("sub", "unknown"),
            "username": claims.get("cognito:username", "unknown"),
            "groups": groups,
            "given_name": claims.get("given_name", ""),
            "family_name": claims.get("family_name", ""),
            "department": claims.get("custom:department", ""),
            "job_title": claims.get("custom:job_title", ""),
        }
    except Exception as e:
        print(f"Error extracting user from event: {e}")
        return {
            "email": "unknown",
            "userId": "unknown",
            "username": "unknown",
            "groups": [],
            "given_name": "",
            "family_name": "",
            "department": "",
            "job_title": "",
        }


def get_user_roles(user: Dict) -> List[DRSRole]:
    """Get DRS roles for a user based on their Cognito groups"""
    user_groups = user.get("groups", [])
    roles = []

    # Map Cognito group names to DRS orchestration roles
    group_to_role_mapping = {
        # New DRS Orchestration Roles (intuitive for disaster recovery teams)
        "DRSOrchestrationAdmin": DRSRole.DRS_ORCHESTRATION_ADMIN,
        "DRSRecoveryManager": DRSRole.DRS_RECOVERY_MANAGER,
        "DRSPlanManager": DRSRole.DRS_PLAN_MANAGER,
        "DRSOperator": DRSRole.DRS_OPERATOR,
        "DRSReadOnly": DRSRole.DRS_READ_ONLY,
        # Legacy AWS-style role names for security test compatibility
        "aws:admin": DRSRole.DRS_ORCHESTRATION_ADMIN,  # Maps to full admin
        "aws:admin-limited": DRSRole.DRS_RECOVERY_MANAGER,  # Maps to recovery manager
        "aws:power-user": DRSRole.DRS_PLAN_MANAGER,  # Maps to plan manager
        "aws:operator": DRSRole.DRS_OPERATOR,  # Maps to operator
        "aws:read-only": DRSRole.DRS_READ_ONLY,  # Maps to read-only
        # Legacy DRS group names (for backward compatibility)
        "DRS-Administrator": DRSRole.DRS_ORCHESTRATION_ADMIN,
        "DRS-Infrastructure-Admin": DRSRole.DRS_RECOVERY_MANAGER,
        "DRS-Recovery-Plan-Manager": DRSRole.DRS_PLAN_MANAGER,
        "DRS-Operator": DRSRole.DRS_OPERATOR,
        "DRS-Read-Only": DRSRole.DRS_READ_ONLY,
    }

    for group in user_groups:
        print(f"🔍 Processing group: '{group}' (length: {len(group)})")
        if group in group_to_role_mapping:
            roles.append(group_to_role_mapping[group])
            print(
                f"✅ Mapped group '{group}' to role: {group_to_role_mapping[group].value}"
            )
        else:
            print(f"⚠️ Unknown group: '{group}'")

    return roles


def get_user_permissions(user: Dict) -> List[DRSPermission]:
    """Get all permissions for a user based on their roles"""
    roles = get_user_roles(user)
    permissions = set()

    for role in roles:
        role_perms = ROLE_PERMISSIONS.get(role, [])
        permissions.update(role_perms)

    return list(permissions)


def has_permission(user: Dict, required_permission: DRSPermission) -> bool:
    """Check if user has a specific permission"""
    user_permissions = get_user_permissions(user)
    return required_permission in user_permissions


def has_any_permission(
    user: Dict, required_permissions: List[DRSPermission]
) -> bool:
    """Check if user has any of the required permissions"""
    user_permissions = get_user_permissions(user)
    return any(perm in user_permissions for perm in required_permissions)


def get_endpoint_permissions(method: str, path: str) -> List[DRSPermission]:
    """Get required permissions for an API endpoint"""
    import re

    # Static path segments that should NOT be normalized to {id}
    # These are the actual API resource names
    STATIC_SEGMENTS = {
        "protection-groups",
        "recovery-plans",
        "executions",
        "accounts",
        "targets",
        "current",
        "drs",
        "source-servers",
        "quotas",
        "ec2",
        "subnets",
        "security-groups",
        "instance-profiles",
        "instance-types",
        "config",
        "export",
        "import",
        "user",
        "permissions",
        "health",
        "resolve",
        "execute",
        "cancel",
        "pause",
        "resume",
        "terminate-instances",
        "job-logs",
        "termination-status",
        "recovery-instances",
        "check-existing-instances",
        "validate",
        "tag-sync",
        "delete",
    }

    # First, try exact match (for paths without dynamic segments)
    endpoint_key = (method, path)
    if endpoint_key in ENDPOINT_PERMISSIONS:
        return ENDPOINT_PERMISSIONS[endpoint_key]

    # Normalize path by replacing dynamic path parameters with placeholders
    # Split path into segments and process each
    segments = path.strip("/").split("/")
    normalized_segments = []

    for i, segment in enumerate(segments):
        # Keep static segments as-is
        if segment.lower() in STATIC_SEGMENTS:
            normalized_segments.append(segment)
        # UUID pattern (36 chars with hyphens)
        elif re.match(r"^[a-f0-9-]{36}$", segment, re.IGNORECASE):
            # Determine placeholder based on context
            if i > 0 and normalized_segments:
                prev = normalized_segments[-1]
                if prev == "executions":
                    normalized_segments.append("{executionId}")
                else:
                    normalized_segments.append("{id}")
            else:
                normalized_segments.append("{id}")
        # Execution ID pattern (exec-xxx or similar)
        elif re.match(r"^exec-[a-zA-Z0-9-]+$", segment, re.IGNORECASE):
            normalized_segments.append("{executionId}")
        # Account ID pattern (acc-xxx or 12-digit AWS account)
        elif re.match(r"^(acc-[a-zA-Z0-9-]+|\d{12})$", segment):
            normalized_segments.append("{id}")
        # Protection group ID pattern (pg-xxx)
        elif re.match(r"^pg-[a-zA-Z0-9-]+$", segment, re.IGNORECASE):
            normalized_segments.append("{id}")
        # Recovery plan ID pattern (plan-xxx)
        elif re.match(r"^plan-[a-zA-Z0-9-]+$", segment, re.IGNORECASE):
            normalized_segments.append("{id}")
        # Generic alphanumeric ID (but NOT static segments)
        elif re.match(r"^[a-zA-Z0-9_-]+$", segment) and len(segment) > 20:
            # Long alphanumeric strings are likely IDs
            if i > 0 and normalized_segments:
                prev = normalized_segments[-1]
                if prev == "executions":
                    normalized_segments.append("{executionId}")
                else:
                    normalized_segments.append("{id}")
            else:
                normalized_segments.append("{id}")
        else:
            # Keep as-is (could be a static segment we don't know about)
            normalized_segments.append(segment)

    normalized_path = "/" + "/".join(normalized_segments) if normalized_segments else "/"

    # Try normalized path
    endpoint_key = (method, normalized_path)
    if endpoint_key in ENDPOINT_PERMISSIONS:
        return ENDPOINT_PERMISSIONS[endpoint_key]

    # Handle specific execution action patterns
    if "/executions/" in path:
        if path.endswith("/cancel"):
            return ENDPOINT_PERMISSIONS.get(
                (method, "/executions/{executionId}/cancel"), []
            )
        elif path.endswith("/pause"):
            return ENDPOINT_PERMISSIONS.get(
                (method, "/executions/{executionId}/pause"), []
            )
        elif path.endswith("/resume"):
            return ENDPOINT_PERMISSIONS.get(
                (method, "/executions/{executionId}/resume"), []
            )
        elif path.endswith("/terminate-instances"):
            return ENDPOINT_PERMISSIONS.get(
                (method, "/executions/{executionId}/terminate-instances"), []
            )
        elif path.endswith("/job-logs"):
            return ENDPOINT_PERMISSIONS.get(
                (method, "/executions/{executionId}/job-logs"), []
            )
        elif path.endswith("/termination-status"):
            return ENDPOINT_PERMISSIONS.get(
                (method, "/executions/{executionId}/termination-status"), []
            )
        elif path.endswith("/recovery-instances"):
            return ENDPOINT_PERMISSIONS.get(
                (method, "/executions/{executionId}/recovery-instances"), []
            )
        # Single execution by ID
        elif path.count("/") == 2:
            return ENDPOINT_PERMISSIONS.get(
                (method, "/executions/{executionId}"), []
            )

    # Handle protection groups with ID
    if "/protection-groups/" in path:
        if path.endswith("/resolve"):
            return ENDPOINT_PERMISSIONS.get(
                (method, "/protection-groups/resolve"), []
            )
        return ENDPOINT_PERMISSIONS.get(
            (method, "/protection-groups/{id}"), []
        )

    # Handle recovery plans with ID
    if "/recovery-plans/" in path:
        if path.endswith("/execute"):
            return ENDPOINT_PERMISSIONS.get(
                (method, "/recovery-plans/{id}/execute"), []
            )
        if path.endswith("/check-existing-instances"):
            return ENDPOINT_PERMISSIONS.get(
                (method, "/recovery-plans/{id}/check-existing-instances"), []
            )
        return ENDPOINT_PERMISSIONS.get(
            (method, "/recovery-plans/{id}"), []
        )

    # Handle accounts/targets with ID
    if "/accounts/targets/" in path:
        if path.endswith("/validate"):
            return ENDPOINT_PERMISSIONS.get(
                (method, "/accounts/targets/{id}/validate"), []
            )
        return ENDPOINT_PERMISSIONS.get(
            (method, "/accounts/targets/{id}"), []
        )

    # No permissions found - return empty list
    return []


def check_authorization(event: Dict) -> Dict:
    """
    Check if the user is authorized to access the requested endpoint
    Returns authorization result with user info and permissions
    
    TIGHT SECURITY: All endpoints require explicit permissions for proper access control.
    Zero-trust model - deny access if no permissions are defined for the endpoint.
    """
    try:
        # Extract request info
        method = event.get("httpMethod", "GET")
        path = event.get("path", "/")

        # Skip authorization for health check and OPTIONS requests
        if path == "/health" or method == "OPTIONS":
            return {
                "authorized": True,
                "user": {
                    "email": "system",
                    "userId": "system",
                    "username": "system",
                },
                "reason": "Public endpoint",
            }

        # Extract user information
        user = get_user_from_event(event)

        # Get required permissions for this endpoint
        required_permissions = get_endpoint_permissions(method, path)

        # TIGHT SECURITY: All endpoints must have explicit permissions defined
        if not required_permissions:
            print(f"❌ No permissions defined for {method} {path} - denying access")
            return {
                "authorized": False,
                "user": user,
                "reason": f"No permissions defined for endpoint {method} {path}",
            }

        # Check if user has required permissions
        if has_any_permission(user, required_permissions):
            return {
                "authorized": True,
                "user": user,
                "permissions": [p.value for p in get_user_permissions(user)],
                "roles": [r.value for r in get_user_roles(user)],
            }
        else:
            return {
                "authorized": False,
                "user": user,
                "reason": f"Missing required permissions: {[p.value for p in required_permissions]}",
                "user_permissions": [
                    p.value for p in get_user_permissions(user)
                ],
                "user_roles": [r.value for r in get_user_roles(user)],
            }

    except Exception as e:
        print(f"Error in authorization check: {e}")
        return {
            "authorized": False,
            "user": {
                "email": "unknown",
                "userId": "unknown",
                "username": "unknown",
            },
            "reason": f"Authorization error: {str(e)}",
        }


def require_permission(required_permission: DRSPermission):
    """Decorator to require specific permission for a function"""

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(event: Dict, *args, **kwargs):
            auth_result = check_authorization(event)

            if not auth_result["authorized"]:
                return {
                    "statusCode": 403,
                    "headers": {
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Headers": "Content-Type,Authorization",
                        "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
                    },
                    "body": json.dumps(
                        {
                            "error": "Forbidden",
                            "message": auth_result["reason"],
                            "required_permission": required_permission.value,
                        }
                    ),
                }

            # Add user info to event for use in the function
            event["user"] = auth_result["user"]
            return func(event, *args, **kwargs)

        return wrapper

    return decorator


def require_any_permission(required_permissions: List[DRSPermission]):
    """Decorator to require any of the specified permissions"""

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(event: Dict, *args, **kwargs):
            auth_result = check_authorization(event)

            if not auth_result["authorized"]:
                return {
                    "statusCode": 403,
                    "headers": {
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Headers": "Content-Type,Authorization",
                        "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
                    },
                    "body": json.dumps(
                        {
                            "error": "Forbidden",
                            "message": auth_result["reason"],
                            "required_permissions": [
                                p.value for p in required_permissions
                            ],
                        }
                    ),
                }

            # Add user info to event for use in the function
            event["user"] = auth_result["user"]
            return func(event, *args, **kwargs)

        return wrapper

    return decorator


def require_role(required_role: DRSRole):
    """Decorator to require specific role for a function"""

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(event: Dict, *args, **kwargs):
            user = get_user_from_event(event)
            user_roles = get_user_roles(user)

            if required_role not in user_roles:
                return {
                    "statusCode": 403,
                    "headers": {
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Headers": "Content-Type,Authorization",
                        "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
                    },
                    "body": json.dumps(
                        {
                            "error": "Forbidden",
                            "message": f"Required role: {required_role.value}",
                            "user_roles": [r.value for r in user_roles],
                        }
                    ),
                }

            # Add user info to event for use in the function
            event["user"] = user
            return func(event, *args, **kwargs)

        return wrapper

    return decorator


# Convenience functions for common role checks
def is_administrator(user: Dict) -> bool:
    """Check if user is a DRS orchestration administrator"""
    return DRSRole.DRS_ORCHESTRATION_ADMIN in get_user_roles(user)


def is_recovery_manager_or_above(user: Dict) -> bool:
    """Check if user is recovery manager or has higher privileges"""
    user_roles = get_user_roles(user)
    privileged_roles = [
        DRSRole.DRS_ORCHESTRATION_ADMIN,
        DRSRole.DRS_RECOVERY_MANAGER,
    ]
    return any(role in user_roles for role in privileged_roles)


def is_operator_or_above(user: Dict) -> bool:
    """Check if user is operator or has higher privileges"""
    user_roles = get_user_roles(user)
    operator_roles = [
        DRSRole.DRS_ORCHESTRATION_ADMIN,
        DRSRole.DRS_RECOVERY_MANAGER,
        DRSRole.DRS_PLAN_MANAGER,
        DRSRole.DRS_OPERATOR,
    ]
    return any(role in user_roles for role in operator_roles)


def can_execute_recovery_plans(user: Dict) -> bool:
    """Check if user can execute recovery plans"""
    return has_permission(user, DRSPermission.START_RECOVERY)


def can_manage_infrastructure(user: Dict) -> bool:
    """Check if user can manage infrastructure (protection groups, recovery plans)"""
    return has_any_permission(
        user,
        [
            DRSPermission.CREATE_PROTECTION_GROUPS,
            DRSPermission.CREATE_RECOVERY_PLANS,
        ],
    )


def can_manage_accounts(user: Dict) -> bool:
    """Check if user can manage target accounts"""
    return has_any_permission(
        user,
        [
            DRSPermission.REGISTER_ACCOUNTS,
            DRSPermission.DELETE_ACCOUNTS,
            DRSPermission.MODIFY_ACCOUNTS,
        ],
    )


def can_terminate_instances(user: Dict) -> bool:
    """Check if user can terminate recovery instances"""
    return has_permission(user, DRSPermission.TERMINATE_INSTANCES)


def get_role_description(role: DRSRole) -> str:
    """Get human-readable description for a DRS orchestration role"""
    descriptions = {
        DRSRole.DRS_ORCHESTRATION_ADMIN: "Full administrative access to all DRS orchestration functions including account management",
        DRSRole.DRS_RECOVERY_MANAGER: "Can execute and manage all recovery operations, register accounts, and manage infrastructure",
        DRSRole.DRS_PLAN_MANAGER: "Can create, modify, and delete recovery plans and protection groups, execute recovery operations",
        DRSRole.DRS_OPERATOR: "Can execute recovery operations and modify existing plans but cannot create/delete or terminate instances",
        DRSRole.DRS_READ_ONLY: "View-only access to all DRS configuration, executions, and status for monitoring and compliance",
    }
    return descriptions.get(role, "Unknown role")
