"""
RBAC Middleware for AWS DRS Orchestration
Implements role-based access control using Cognito Groups
"""

import json
from typing import Dict, List, Optional, Callable
from functools import wraps
from enum import Enum

class DRSRole(Enum):
    """DRS Role definitions for disaster recovery operations"""
    ADMINISTRATOR = "DRS-Administrator"
    INFRASTRUCTURE_ADMIN = "DRS-Infrastructure-Admin"
    RECOVERY_PLAN_MANAGER = "DRS-Recovery-Plan-Manager"
    OPERATOR = "DRS-Operator"
    RECOVERY_PLAN_VIEWER = "DRS-Recovery-Plan-Viewer"
    READ_ONLY = "DRS-Read-Only"

class DRSPermission(Enum):
    """DRS Permission definitions"""
    # Protection Groups
    PROTECTION_GROUPS_CREATE = "protection_groups:create"
    PROTECTION_GROUPS_READ = "protection_groups:read"
    PROTECTION_GROUPS_UPDATE = "protection_groups:update"
    PROTECTION_GROUPS_DELETE = "protection_groups:delete"
    
    # Recovery Plans
    RECOVERY_PLANS_CREATE = "recovery_plans:create"
    RECOVERY_PLANS_READ = "recovery_plans:read"
    RECOVERY_PLANS_UPDATE = "recovery_plans:update"
    RECOVERY_PLANS_DELETE = "recovery_plans:delete"
    RECOVERY_PLANS_EXECUTE = "recovery_plans:execute"
    
    # Executions
    EXECUTIONS_CREATE = "executions:create"
    EXECUTIONS_READ = "executions:read"
    EXECUTIONS_CANCEL = "executions:cancel"
    EXECUTIONS_PAUSE = "executions:pause"
    EXECUTIONS_RESUME = "executions:resume"
    EXECUTIONS_DELETE = "executions:delete"
    EXECUTIONS_TERMINATE_INSTANCES = "executions:terminate_instances"
    
    # DRS Operations
    DRS_SOURCE_SERVERS_READ = "drs:source_servers_read"
    DRS_QUOTAS_READ = "drs:quotas_read"
    DRS_TAG_SYNC = "drs:tag_sync"
    DRS_ACCOUNTS_READ = "drs:accounts_read"
    
    # EC2 Operations
    EC2_RESOURCES_READ = "ec2:resources_read"
    
    # Configuration
    CONFIG_EXPORT = "config:export"
    CONFIG_IMPORT = "config:import"
    
    # User Management
    USERS_PROFILE_READ = "users:profile_read"
    USERS_ROLES_READ = "users:roles_read"

# Role-Permission Matrix (Disaster Recovery Style)
ROLE_PERMISSIONS = {
    DRSRole.ADMINISTRATOR: [
        # Full access to everything
        DRSPermission.PROTECTION_GROUPS_CREATE,
        DRSPermission.PROTECTION_GROUPS_READ,
        DRSPermission.PROTECTION_GROUPS_UPDATE,
        DRSPermission.PROTECTION_GROUPS_DELETE,
        DRSPermission.RECOVERY_PLANS_CREATE,
        DRSPermission.RECOVERY_PLANS_READ,
        DRSPermission.RECOVERY_PLANS_UPDATE,
        DRSPermission.RECOVERY_PLANS_DELETE,
        DRSPermission.RECOVERY_PLANS_EXECUTE,
        DRSPermission.EXECUTIONS_CREATE,
        DRSPermission.EXECUTIONS_READ,
        DRSPermission.EXECUTIONS_CANCEL,
        DRSPermission.EXECUTIONS_PAUSE,
        DRSPermission.EXECUTIONS_RESUME,
        DRSPermission.EXECUTIONS_DELETE,
        DRSPermission.EXECUTIONS_TERMINATE_INSTANCES,
        DRSPermission.DRS_SOURCE_SERVERS_READ,
        DRSPermission.DRS_QUOTAS_READ,
        DRSPermission.DRS_TAG_SYNC,
        DRSPermission.DRS_ACCOUNTS_READ,
        DRSPermission.EC2_RESOURCES_READ,
        DRSPermission.CONFIG_EXPORT,
        DRSPermission.CONFIG_IMPORT,
        DRSPermission.USERS_PROFILE_READ,
        DRSPermission.USERS_ROLES_READ,
    ],
    
    DRSRole.INFRASTRUCTURE_ADMIN: [
        # Can manage infrastructure and configuration
        DRSPermission.PROTECTION_GROUPS_CREATE,
        DRSPermission.PROTECTION_GROUPS_READ,
        DRSPermission.PROTECTION_GROUPS_UPDATE,
        DRSPermission.PROTECTION_GROUPS_DELETE,
        DRSPermission.RECOVERY_PLANS_CREATE,
        DRSPermission.RECOVERY_PLANS_READ,
        DRSPermission.RECOVERY_PLANS_UPDATE,
        DRSPermission.RECOVERY_PLANS_DELETE,
        DRSPermission.RECOVERY_PLANS_EXECUTE,
        DRSPermission.EXECUTIONS_READ,
        DRSPermission.DRS_SOURCE_SERVERS_READ,
        DRSPermission.DRS_QUOTAS_READ,
        DRSPermission.DRS_TAG_SYNC,
        DRSPermission.DRS_ACCOUNTS_READ,
        DRSPermission.EC2_RESOURCES_READ,
        DRSPermission.CONFIG_EXPORT,
        DRSPermission.CONFIG_IMPORT,
        DRSPermission.USERS_PROFILE_READ,
        DRSPermission.USERS_ROLES_READ,
    ],
    
    DRSRole.RECOVERY_PLAN_MANAGER: [
        # Can create, modify, and execute recovery plans
        DRSPermission.PROTECTION_GROUPS_READ,
        DRSPermission.RECOVERY_PLANS_CREATE,
        DRSPermission.RECOVERY_PLANS_READ,
        DRSPermission.RECOVERY_PLANS_UPDATE,
        DRSPermission.RECOVERY_PLANS_DELETE,
        DRSPermission.RECOVERY_PLANS_EXECUTE,
        DRSPermission.EXECUTIONS_CREATE,
        DRSPermission.EXECUTIONS_READ,
        DRSPermission.EXECUTIONS_CANCEL,
        DRSPermission.EXECUTIONS_PAUSE,
        DRSPermission.EXECUTIONS_RESUME,
        DRSPermission.EXECUTIONS_TERMINATE_INSTANCES,
        DRSPermission.DRS_SOURCE_SERVERS_READ,
        DRSPermission.DRS_QUOTAS_READ,
        DRSPermission.EC2_RESOURCES_READ,
        DRSPermission.USERS_PROFILE_READ,
        DRSPermission.USERS_ROLES_READ,
    ],
    
    DRSRole.OPERATOR: [
        # Can execute recovery plans and perform DR operations
        DRSPermission.PROTECTION_GROUPS_READ,
        DRSPermission.RECOVERY_PLANS_READ,
        DRSPermission.RECOVERY_PLANS_EXECUTE,
        DRSPermission.EXECUTIONS_CREATE,
        DRSPermission.EXECUTIONS_READ,
        DRSPermission.EXECUTIONS_CANCEL,
        DRSPermission.EXECUTIONS_PAUSE,
        DRSPermission.EXECUTIONS_RESUME,
        DRSPermission.EXECUTIONS_TERMINATE_INSTANCES,
        DRSPermission.DRS_SOURCE_SERVERS_READ,
        DRSPermission.DRS_QUOTAS_READ,
        DRSPermission.EC2_RESOURCES_READ,
        DRSPermission.USERS_PROFILE_READ,
        DRSPermission.USERS_ROLES_READ,
    ],
    
    DRSRole.RECOVERY_PLAN_VIEWER: [
        # Can view recovery plans but not execute them
        DRSPermission.PROTECTION_GROUPS_READ,
        DRSPermission.RECOVERY_PLANS_READ,
        DRSPermission.EXECUTIONS_READ,
        DRSPermission.DRS_SOURCE_SERVERS_READ,
        DRSPermission.DRS_QUOTAS_READ,
        DRSPermission.EC2_RESOURCES_READ,
        DRSPermission.USERS_PROFILE_READ,
        DRSPermission.USERS_ROLES_READ,
    ],
    
    DRSRole.READ_ONLY: [
        # View-only access to DRS configuration and status
        DRSPermission.PROTECTION_GROUPS_READ,
        DRSPermission.RECOVERY_PLANS_READ,
        DRSPermission.EXECUTIONS_READ,
        DRSPermission.DRS_SOURCE_SERVERS_READ,
        DRSPermission.DRS_QUOTAS_READ,
        DRSPermission.EC2_RESOURCES_READ,
        DRSPermission.USERS_PROFILE_READ,
        DRSPermission.USERS_ROLES_READ,
    ],
}

# API Endpoint to Permission Mapping
ENDPOINT_PERMISSIONS = {
    # Protection Groups
    ('GET', '/protection-groups'): [DRSPermission.PROTECTION_GROUPS_READ],
    ('POST', '/protection-groups'): [DRSPermission.PROTECTION_GROUPS_CREATE],
    ('GET', '/protection-groups/{id}'): [DRSPermission.PROTECTION_GROUPS_READ],
    ('PUT', '/protection-groups/{id}'): [DRSPermission.PROTECTION_GROUPS_UPDATE],
    ('DELETE', '/protection-groups/{id}'): [DRSPermission.PROTECTION_GROUPS_DELETE],
    ('POST', '/protection-groups/{id}'): [DRSPermission.PROTECTION_GROUPS_UPDATE],  # resolve endpoint
    
    # Recovery Plans
    ('GET', '/recovery-plans'): [DRSPermission.RECOVERY_PLANS_READ],
    ('POST', '/recovery-plans'): [DRSPermission.RECOVERY_PLANS_CREATE],
    ('GET', '/recovery-plans/{id}'): [DRSPermission.RECOVERY_PLANS_READ],
    ('PUT', '/recovery-plans/{id}'): [DRSPermission.RECOVERY_PLANS_UPDATE],
    ('DELETE', '/recovery-plans/{id}'): [DRSPermission.RECOVERY_PLANS_DELETE],
    ('POST', '/recovery-plans/{id}/execute'): [DRSPermission.RECOVERY_PLANS_EXECUTE],
    ('GET', '/recovery-plans/{id}/check-existing-instances'): [DRSPermission.RECOVERY_PLANS_READ],
    
    # Executions
    ('GET', '/executions'): [DRSPermission.EXECUTIONS_READ],
    ('POST', '/executions'): [DRSPermission.EXECUTIONS_CREATE],
    ('DELETE', '/executions'): [DRSPermission.EXECUTIONS_DELETE],
    ('POST', '/executions/delete'): [DRSPermission.EXECUTIONS_DELETE],
    ('GET', '/executions/{executionId}'): [DRSPermission.EXECUTIONS_READ],
    ('POST', '/executions/{executionId}/cancel'): [DRSPermission.EXECUTIONS_CANCEL],
    ('POST', '/executions/{executionId}/pause'): [DRSPermission.EXECUTIONS_PAUSE],
    ('POST', '/executions/{executionId}/resume'): [DRSPermission.EXECUTIONS_RESUME],
    ('POST', '/executions/{executionId}/terminate-instances'): [DRSPermission.EXECUTIONS_TERMINATE_INSTANCES],
    ('GET', '/executions/{executionId}/job-logs'): [DRSPermission.EXECUTIONS_READ],
    ('GET', '/executions/{executionId}/termination-status'): [DRSPermission.EXECUTIONS_READ],
    
    # DRS Operations
    ('GET', '/drs/source-servers'): [DRSPermission.DRS_SOURCE_SERVERS_READ],
    ('GET', '/drs/quotas'): [DRSPermission.DRS_QUOTAS_READ],
    ('POST', '/drs/tag-sync'): [DRSPermission.DRS_TAG_SYNC],
    ('GET', '/drs/accounts'): [DRSPermission.DRS_ACCOUNTS_READ],
    
    # EC2 Operations
    ('GET', '/ec2/subnets'): [DRSPermission.EC2_RESOURCES_READ],
    ('GET', '/ec2/security-groups'): [DRSPermission.EC2_RESOURCES_READ],
    ('GET', '/ec2/instance-profiles'): [DRSPermission.EC2_RESOURCES_READ],
    ('GET', '/ec2/instance-types'): [DRSPermission.EC2_RESOURCES_READ],
    
    # Configuration
    ('GET', '/config/export'): [DRSPermission.CONFIG_EXPORT],
    ('POST', '/config/import'): [DRSPermission.CONFIG_IMPORT],
    
    # Accounts
    ('GET', '/accounts/targets'): [DRSPermission.DRS_ACCOUNTS_READ],
    ('POST', '/accounts/targets'): [DRSPermission.DRS_ACCOUNTS_READ],  # Admin only in practice
    ('PUT', '/accounts/targets/{id}'): [DRSPermission.DRS_ACCOUNTS_READ],  # Admin only in practice
    ('DELETE', '/accounts/targets/{id}'): [DRSPermission.DRS_ACCOUNTS_READ],  # Admin only in practice
    ('POST', '/accounts/targets/{id}/validate'): [DRSPermission.DRS_ACCOUNTS_READ],
    
    # User Management
    ('GET', '/users/profile'): [DRSPermission.USERS_PROFILE_READ],
    ('GET', '/users/roles'): [DRSPermission.USERS_ROLES_READ],
}

def get_user_from_event(event: Dict) -> Dict:
    """Extract user information from API Gateway event"""
    try:
        authorizer = event.get('requestContext', {}).get('authorizer', {})
        claims = authorizer.get('claims', {})
        
        # Extract groups from cognito:groups claim
        groups_claim = claims.get('cognito:groups', '')
        groups = groups_claim.split(',') if groups_claim else []
        
        return {
            'email': claims.get('email', 'unknown'),
            'userId': claims.get('sub', 'unknown'),
            'username': claims.get('cognito:username', 'unknown'),
            'groups': groups,
            'given_name': claims.get('given_name', ''),
            'family_name': claims.get('family_name', ''),
            'department': claims.get('custom:department', ''),
            'job_title': claims.get('custom:job_title', ''),
        }
    except Exception as e:
        print(f"Error extracting user from event: {e}")
        return {
            'email': 'unknown',
            'userId': 'unknown', 
            'username': 'unknown',
            'groups': [],
            'given_name': '',
            'family_name': '',
            'department': '',
            'job_title': '',
        }

def get_user_roles(user: Dict) -> List[DRSRole]:
    """Get DRS roles for a user based on their Cognito groups"""
    user_groups = user.get('groups', [])
    roles = []
    
    for group in user_groups:
        try:
            role = DRSRole(group)
            roles.append(role)
        except ValueError:
            # Group is not a recognized DRS role
            continue
    
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

def has_any_permission(user: Dict, required_permissions: List[DRSPermission]) -> bool:
    """Check if user has any of the required permissions"""
    user_permissions = get_user_permissions(user)
    return any(perm in user_permissions for perm in required_permissions)

def get_endpoint_permissions(method: str, path: str) -> List[DRSPermission]:
    """Get required permissions for an API endpoint"""
    # Normalize path by replacing path parameters with {id}
    normalized_path = path
    
    # Replace common path parameters
    import re
    normalized_path = re.sub(r'/[a-f0-9-]{36}', '/{id}', normalized_path)  # UUIDs
    normalized_path = re.sub(r'/[a-zA-Z0-9-]+(?=/|$)', '/{id}', normalized_path)  # Generic IDs
    
    # Handle specific patterns
    if '/executions/' in path and path.count('/') >= 3:
        if path.endswith('/cancel'):
            normalized_path = '/executions/{executionId}/cancel'
        elif path.endswith('/pause'):
            normalized_path = '/executions/{executionId}/pause'
        elif path.endswith('/resume'):
            normalized_path = '/executions/{executionId}/resume'
        elif path.endswith('/terminate-instances'):
            normalized_path = '/executions/{executionId}/terminate-instances'
        elif path.endswith('/job-logs'):
            normalized_path = '/executions/{executionId}/job-logs'
        elif path.endswith('/termination-status'):
            normalized_path = '/executions/{executionId}/termination-status'
        else:
            normalized_path = '/executions/{executionId}'
    
    endpoint_key = (method, normalized_path)
    return ENDPOINT_PERMISSIONS.get(endpoint_key, [])

def check_authorization(event: Dict) -> Dict:
    """
    Check if the user is authorized to access the requested endpoint
    Returns authorization result with user info and permissions
    """
    try:
        # Extract request info
        method = event.get('httpMethod', 'GET')
        path = event.get('path', '/')
        
        # Skip authorization for health check and OPTIONS requests
        if path == '/health' or method == 'OPTIONS':
            return {
                'authorized': True,
                'user': {'email': 'system', 'userId': 'system', 'username': 'system'},
                'reason': 'Public endpoint'
            }
        
        # Extract user information
        user = get_user_from_event(event)
        
        # Get required permissions for this endpoint
        required_permissions = get_endpoint_permissions(method, path)
        
        # If no specific permissions required, allow access (fallback)
        if not required_permissions:
            print(f"⚠️ No permissions defined for {method} {path}, allowing access")
            return {
                'authorized': True,
                'user': user,
                'reason': 'No specific permissions required'
            }
        
        # Check if user has required permissions
        if has_any_permission(user, required_permissions):
            return {
                'authorized': True,
                'user': user,
                'permissions': [p.value for p in get_user_permissions(user)],
                'roles': [r.value for r in get_user_roles(user)]
            }
        else:
            return {
                'authorized': False,
                'user': user,
                'reason': f'Missing required permissions: {[p.value for p in required_permissions]}',
                'user_permissions': [p.value for p in get_user_permissions(user)],
                'user_roles': [r.value for r in get_user_roles(user)]
            }
            
    except Exception as e:
        print(f"Error in authorization check: {e}")
        return {
            'authorized': False,
            'user': {'email': 'unknown', 'userId': 'unknown', 'username': 'unknown'},
            'reason': f'Authorization error: {str(e)}'
        }

def require_permission(required_permission: DRSPermission):
    """Decorator to require specific permission for a function"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(event: Dict, *args, **kwargs):
            auth_result = check_authorization(event)
            
            if not auth_result['authorized']:
                return {
                    'statusCode': 403,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
                    },
                    'body': json.dumps({
                        'error': 'Forbidden',
                        'message': auth_result['reason'],
                        'required_permission': required_permission.value
                    })
                }
            
            # Add user info to event for use in the function
            event['user'] = auth_result['user']
            return func(event, *args, **kwargs)
        
        return wrapper
    return decorator

def require_any_permission(required_permissions: List[DRSPermission]):
    """Decorator to require any of the specified permissions"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(event: Dict, *args, **kwargs):
            auth_result = check_authorization(event)
            
            if not auth_result['authorized']:
                return {
                    'statusCode': 403,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
                    },
                    'body': json.dumps({
                        'error': 'Forbidden',
                        'message': auth_result['reason'],
                        'required_permissions': [p.value for p in required_permissions]
                    })
                }
            
            # Add user info to event for use in the function
            event['user'] = auth_result['user']
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
                    'statusCode': 403,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
                    },
                    'body': json.dumps({
                        'error': 'Forbidden',
                        'message': f'Required role: {required_role.value}',
                        'user_roles': [r.value for r in user_roles]
                    })
                }
            
            # Add user info to event for use in the function
            event['user'] = user
            return func(event, *args, **kwargs)
        
        return wrapper
    return decorator

# Convenience functions for common role checks
def is_administrator(user: Dict) -> bool:
    """Check if user is an administrator"""
    return DRSRole.ADMINISTRATOR in get_user_roles(user)

def is_operator_or_above(user: Dict) -> bool:
    """Check if user is operator or has higher privileges"""
    user_roles = get_user_roles(user)
    operator_roles = [
        DRSRole.ADMINISTRATOR,
        DRSRole.INFRASTRUCTURE_ADMIN,
        DRSRole.RECOVERY_PLAN_MANAGER,
        DRSRole.OPERATOR
    ]
    return any(role in user_roles for role in operator_roles)

def can_execute_recovery_plans(user: Dict) -> bool:
    """Check if user can execute recovery plans"""
    return has_permission(user, DRSPermission.RECOVERY_PLANS_EXECUTE)

def can_manage_infrastructure(user: Dict) -> bool:
    """Check if user can manage infrastructure (protection groups, recovery plans)"""
    return has_any_permission(user, [
        DRSPermission.PROTECTION_GROUPS_CREATE,
        DRSPermission.RECOVERY_PLANS_CREATE
    ])

# User profile and roles endpoints
def get_user_profile(event: Dict) -> Dict:
    """Get current user profile information"""
    user = get_user_from_event(event)
    roles = get_user_roles(user)
    permissions = get_user_permissions(user)
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        },
        'body': json.dumps({
            'user': {
                'email': user['email'],
                'username': user['username'],
                'given_name': user['given_name'],
                'family_name': user['family_name'],
                'department': user['department'],
                'job_title': user['job_title'],
            },
            'roles': [r.value for r in roles],
            'permissions': [p.value for p in permissions],
            'capabilities': {
                'is_administrator': is_administrator(user),
                'is_operator_or_above': is_operator_or_above(user),
                'can_execute_recovery_plans': can_execute_recovery_plans(user),
                'can_manage_infrastructure': can_manage_infrastructure(user),
            }
        })
    }

def get_user_roles_info(event: Dict) -> Dict:
    """Get detailed role information for current user"""
    user = get_user_from_event(event)
    roles = get_user_roles(user)
    
    role_details = []
    for role in roles:
        permissions = ROLE_PERMISSIONS.get(role, [])
        role_details.append({
            'name': role.value,
            'description': get_role_description(role),
            'permissions': [p.value for p in permissions]
        })
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
        },
        'body': json.dumps({
            'user_roles': role_details,
            'available_roles': [
                {
                    'name': role.value,
                    'description': get_role_description(role)
                }
                for role in DRSRole
            ]
        })
    }

def get_role_description(role: DRSRole) -> str:
    """Get human-readable description for a role"""
    descriptions = {
        DRSRole.ADMINISTRATOR: "Full administrative access to all DRS orchestration functions",
        DRSRole.INFRASTRUCTURE_ADMIN: "Can manage DRS infrastructure, protection groups, and recovery plans",
        DRSRole.RECOVERY_PLAN_MANAGER: "Can create, modify, and execute recovery plans",
        DRSRole.OPERATOR: "Can execute recovery plans and perform DR operations",
        DRSRole.RECOVERY_PLAN_VIEWER: "Can view recovery plans but not execute them",
        DRSRole.READ_ONLY: "View-only access to DRS configuration and status"
    }
    return descriptions.get(role, "Unknown role")