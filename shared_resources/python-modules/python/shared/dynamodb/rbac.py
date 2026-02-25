import os
from typing import List, Optional, Dict, Any

import boto3
from pynamodb.models import Model
from pynamodb.attributes import (
    UnicodeAttribute,
    BooleanAttribute,
    MapAttribute,
)
from pynamodb.indexes import GlobalSecondaryIndex, AllProjection
from shared.utils import ENV_DYNAMO


SESSION = boto3.session.Session()
REGION = SESSION.region_name
dynamodb_client = boto3.client("dynamodb", region_name=REGION)


# ============================================================================
# PynamoDB Models
# ============================================================================


class Role(Model):
    """
    Roles table - stores role definitions
    PK: role_id
    """

    class Meta:
        table_name = ENV_DYNAMO.DYNAMO_ROLES_TABLE
        region = REGION

    role_id = UnicodeAttribute(hash_key=True)
    role_name = UnicodeAttribute(attr_name="role_name")
    role_name_lower = UnicodeAttribute(attr_name="role_name_lower")
    description = UnicodeAttribute(attr_name="description", default="")
    is_active = BooleanAttribute(attr_name="is_active", default=True)

    def to_dict(self):
        return {
            "role_id": self.role_id,
            "role_name": self.role_name,
            "description": self.description,
            "is_active": self.is_active,
        }


class Permission(Model):
    """
    Permissions table - stores all available permissions
    PK: permission_id (e.g., "project_onboarding.create")
    Attributes:
      - disabled: true if this permission combination is invalid
    """

    class Meta:
        table_name = ENV_DYNAMO.DYNAMO_PERMISSIONS_TABLE
        region = REGION

    permission_id = UnicodeAttribute(hash_key=True)
    disabled = BooleanAttribute(default=False)

    def to_dict(self):
        return {
            "permission_id": self.permission_id,
            "disabled": self.disabled,
        }


class PermissionIdIndex(GlobalSecondaryIndex):
    """
    GSI for reverse lookup: which roles have a specific permission?
    """

    class Meta:
        index_name = ENV_DYNAMO.DYNAMO_ROLE_PERMISSIONS_PERM_ID_INDEX
        projection = AllProjection()

    permission_id = UnicodeAttribute(hash_key=True)
    role_id = UnicodeAttribute(range_key=True)


class RolePermission(Model):
    """
    Role-Permission mapping table
    PK: role_id, SK: permission_id
    GSI: permission_id -> role_id (reverse lookup)
    """

    class Meta:
        table_name = ENV_DYNAMO.DYNAMO_ROLE_PERMISSIONS_TABLE
        region = REGION

    role_id = UnicodeAttribute(hash_key=True)
    permission_id = UnicodeAttribute(range_key=True)
    permission_id_index = PermissionIdIndex()

    def to_dict(self):
        return {
            "role_id": self.role_id,
            "permission_id": self.permission_id,
        }


class RoleIdIndex(GlobalSecondaryIndex):
    """
    GSI for reverse lookup: which users have a specific role?
    """

    class Meta:
        index_name = ENV_DYNAMO.DYNAMO_USER_ROLES_ROLE_ID_INDEX
        projection = AllProjection()

    role_id = UnicodeAttribute(hash_key=True)
    uid = UnicodeAttribute(range_key=True)


class UserRole(Model):
    """
    User-Role assignment table
    PK: uid, SK: role_id
    GSI: role_id -> uid (reverse lookup)
    """

    class Meta:
        table_name = ENV_DYNAMO.DYNAMO_USER_ROLES_TABLE
        region = REGION

    uid = UnicodeAttribute(hash_key=True)
    role_id = UnicodeAttribute(range_key=True)
    role_id_index = RoleIdIndex()

    def to_dict(self):
        return {
            "uid": self.uid,
            "role_id": self.role_id,
        }


# ============================================================================
# Helper Functions - Permission Checking
# ============================================================================


def get_user_permissions(uid: str) -> List[str]:
    """
    Get all permissions for a user by resolving their roles.
    
    Args:
        uid: User ID (Cognito sub)
        
    Returns:
        List of permission strings (e.g., ["project_onboarding.create", ...])
    """
    permissions = set()
    
    # Get all roles for this user
    user_roles = list(UserRole.query(uid))
    
    for user_role in user_roles:
        # Get all permissions for this role
        role_permissions = list(RolePermission.query(user_role.role_id))
        permissions.update([rp.permission_id for rp in role_permissions])
    
    return list(permissions)


def check_permission(uid: str, permission_id: str) -> bool:
    """
    Check if a user has a specific permission.
    
    Args:
        uid: User ID (Cognito sub)
        permission_id: Permission string (e.g., "project_onboarding.create")
        
    Returns:
        True if user has the permission, False otherwise
    """
    return permission_id in get_user_permissions(uid)


def check_any_permission(uid: str, permission_ids: List[str]) -> bool:
    """
    Check if a user has ANY of the specified permissions.
    
    Args:
        uid: User ID
        permission_ids: List of permission strings
        
    Returns:
        True if user has at least one permission
    """
    user_permissions = get_user_permissions(uid)
    return any(perm in user_permissions for perm in permission_ids)


def check_all_permissions(uid: str, permission_ids: List[str]) -> bool:
    """
    Check if a user has ALL of the specified permissions.
    
    Args:
        uid: User ID
        permission_ids: List of permission strings
        
    Returns:
        True if user has all permissions
    """
    user_permissions = get_user_permissions(uid)
    return all(perm in user_permissions for perm in permission_ids)


# ============================================================================
# Helper Functions - Role Management
# ============================================================================


def assign_role_to_user(uid: str, role_id: str) -> bool:
    """
    Assign a role to a user.
    
    Args:
        uid: User ID
        role_id: Role ID
        
    Returns:
        True if successful
    """
    try:
        user_role = UserRole(uid, role_id)
        user_role.save()
        return True
    except Exception as e:
        print(f"Error assigning role {role_id} to user {uid}: {e}")
        return False


def remove_role_from_user(uid: str, role_id: str) -> bool:
    """
    Remove a role from a user.
    
    Args:
        uid: User ID
        role_id: Role ID
        
    Returns:
        True if successful
    """
    try:
        user_role = UserRole.get(uid, role_id)
        user_role.delete()
        return True
    except UserRole.DoesNotExist:
        print(f"User {uid} does not have role {role_id}")
        return False
    except Exception as e:
        print(f"Error removing role {role_id} from user {uid}: {e}")
        return False


def get_user_roles(uid: str) -> List[Dict[str, str]]:
    """
    Get all roles assigned to a user.
    
    Args:
        uid: User ID
        
    Returns:
        List of role dictionaries with role details
    """
    user_roles = list(UserRole.query(uid))
    roles = []
    
    for user_role in user_roles:
        try:
            role = Role.get(user_role.role_id)
            roles.append(role.to_dict())
        except Role.DoesNotExist:
            print(f"Role {user_role.role_id} not found")
    
    return roles


def get_users_by_role(role_id: str) -> List[str]:
    """
    Get all users with a specific role.
    
    Args:
        role_id: Role ID
        
    Returns:
        List of user IDs
    """
    user_roles = list(UserRole.role_id_index.query(role_id))
    return [ur.uid for ur in user_roles]


# ============================================================================
# Helper Functions - Role & Permission CRUD
# ============================================================================


def create_role(role_name: str, description: str = "", is_active: bool = True) -> Optional[str]:
    """
    Create a new role.
    
    Args:
        role_name: Name of the role
        description: Description of the role
        is_active: Whether the role is active (default: True)
        
    Returns:
        role_id if successful, None otherwise
    """
    import uuid
    
    try:
        role_id = str(uuid.uuid4())
        role = Role(role_id)
        role.role_name = role_name
        role.role_name_lower = role_name.lower()
        role.description = description
        role.is_active = is_active
        role.save()
        return role_id
    except Exception as e:
        print(f"Error creating role {role_name}: {e}")
        return None


def assign_permission_to_role(role_id: str, permission_id: str) -> bool:
    """
    Assign a permission to a role.
    
    Args:
        role_id: Role ID
        permission_id: Permission string
        
    Returns:
        True if successful
    """
    try:
        role_permission = RolePermission(role_id, permission_id)
        role_permission.save()
        return True
    except Exception as e:
        print(f"Error assigning permission {permission_id} to role {role_id}: {e}")
        return False


def remove_permission_from_role(role_id: str, permission_id: str) -> bool:
    """
    Remove a permission from a role.
    
    Args:
        role_id: Role ID
        permission_id: Permission string
        
    Returns:
        True if successful
    """
    try:
        role_permission = RolePermission.get(role_id, permission_id)
        role_permission.delete()
        return True
    except RolePermission.DoesNotExist:
        print(f"Role {role_id} does not have permission {permission_id}")
        return False
    except Exception as e:
        print(f"Error removing permission {permission_id} from role {role_id}: {e}")
        return False


def get_role_permissions(role_id: str) -> List[str]:
    """
    Get all permissions for a role.
    
    Args:
        role_id: Role ID
        
    Returns:
        List of permission strings
    """
    role_permissions = list(RolePermission.query(role_id))
    return [rp.permission_id for rp in role_permissions]


def list_all_roles(limit: int = None, last_evaluated_key: dict = None, search_term: str = None, status_filter: str = None) -> tuple:
    """
    List all roles in the system with pagination and filtering.
    
    Args:
        limit: Number of items to return
        last_evaluated_key: Key to continue from previous scan
        search_term: Search term for role name (case-insensitive)
        status_filter: Filter by status - "active", "inactive", or None for all
    
    Returns:
        Tuple of (list of role dictionaries, last_evaluated_key)
    """
    params = {}
    if limit:
        params['limit'] = limit
    if last_evaluated_key:
        params['last_evaluated_key'] = last_evaluated_key
    
    # Build filter condition
    filter_conditions = []
    
    if search_term:
        search_lower = search_term.lower()
        filter_conditions.append(Role.role_name_lower.contains(search_lower))
    
    if status_filter == "active":
        filter_conditions.append(Role.is_active == True)
    elif status_filter == "inactive":
        filter_conditions.append(Role.is_active == False)
    
    # Combine filters
    if filter_conditions:
        combined_filter = filter_conditions[0]
        for condition in filter_conditions[1:]:
            combined_filter = combined_filter & condition
        params['filter_condition'] = combined_filter
    
    roles_result = Role.scan(**params)
    roles = [role.to_dict() for role in roles_result]
    
    return roles, roles_result.last_evaluated_key


def list_all_permissions() -> List[str]:
    """
    List all permissions in the system.
    
    Returns:
        List of permission strings
    """
    permissions = list(Permission.scan())
    return [perm.permission_id for perm in permissions]


def list_all_permissions_with_disabled() -> List[dict]:
    """
    List all permissions in the system with disabled flag.
    
    Returns:
        List of dicts: {"permission_id": str, "disabled": bool}
    """
    permissions = list(Permission.scan())
    return [perm.to_dict() for perm in permissions]


# ============================================================================
# Helper Functions - Resource-Action Permission Helpers
# ============================================================================


def check_resource_action(uid: str, resource: str, action: str) -> bool:
    """
    Check if user can perform an action on a resource.
    
    Args:
        uid: User ID
        resource: Resource name (e.g., "project_onboarding")
        action: Action (e.g., "create", "read", "update", "delete", "download")
        
    Returns:
        True if user has permission
    """
    permission_id = f"{resource}.{action}"
    return check_permission(uid, permission_id)


def get_user_resources_by_action(uid: str, action: str) -> List[str]:
    """
    Get all resources a user can perform a specific action on.
    
    Args:
        uid: User ID
        action: Action (e.g., "create", "read")
        
    Returns:
        List of resource names
    """
    permissions = get_user_permissions(uid)
    resources = []
    
    for perm in permissions:
        if perm.endswith(f".{action}"):
            resource = perm.rsplit(".", 1)[0]
            resources.append(resource)
    
    return resources


def get_user_actions_for_resource(uid: str, resource: str) -> List[str]:
    """
    Get all actions a user can perform on a specific resource.
    
    Args:
        uid: User ID
        resource: Resource name
        
    Returns:
        List of actions
    """
    permissions = get_user_permissions(uid)
    actions = []
    
    for perm in permissions:
        if perm.startswith(f"{resource}."):
            action = perm.split(".", 1)[1]
            actions.append(action)
    
    return actions
