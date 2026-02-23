import json
import base64
from functools import wraps
from typing import List, Optional, Union

from shared.utils import ENV_COGNITO
from shared.apiutils import AuthError


# ============================================================================
# JWT Helper Functions
# ============================================================================

def base64url_encode(input: bytes) -> str:
    """Encode bytes to base64url string without padding"""
    return base64.urlsafe_b64encode(input).decode("utf-8").replace("=", "")


def base64url_decode(input: str) -> bytes:
    """Decode base64url string to bytes, adding padding if needed"""
    # Add padding if needed
    padding = 4 - len(input) % 4
    if padding != 4:
        input += "=" * padding
    return base64.urlsafe_b64decode(input)


def create_permissions_token(payload: dict) -> str:
    """
    Create an unsigned JWT token for permissions
    
    Args:
        payload: dict containing 'sub' and 'permissions' keys
        
    Returns:
        JWT token string (unsigned)
    """
    header = {"alg": "none", "typ": "JWT"}
    
    header_json = json.dumps(header, separators=(",", ":")).encode("utf-8")
    payload_json = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    
    header_b64 = base64url_encode(header_json)
    payload_b64 = base64url_encode(payload_json)
    
    return f"{header_b64}.{payload_b64}."


def decode_permissions_token(token: str) -> dict:
    """
    Decode an unsigned JWT token
    
    Args:
        token: JWT token string
        
    Returns:
        dict containing the payload (sub, permissions)
        
    Raises:
        AuthError: if token is invalid or malformed
    """
    try:
        parts = token.split(".")
        if len(parts) < 2:
            raise ValueError("Invalid token format")
        
        payload_b64 = parts[1]
        payload_json = base64url_decode(payload_b64)
        payload = json.loads(payload_json)
        
        return payload
    except Exception as e:
        raise AuthError(
            error_code="InvalidToken",
            error_message=f"Failed to decode permissions token: {str(e)}"
        )


def get_permissions_from_event(event: dict) -> List[str]:
    """
    Extract permissions list from event headers
    
    Args:
        event: Lambda event dict
        
    Returns:
        List of permission strings
        
    Raises:
        AuthError: if token is missing or invalid
    """
    headers = event.get("headers", {})
    
    # Header names can be lowercase or mixed case
    token = headers.get("x-permissions-token") or headers.get("X-Permissions-Token")
    
    if not token:
        raise AuthError(
            error_code="MissingToken",
            error_message="Permissions token is required"
        )
    
    payload = decode_permissions_token(token)
    return payload.get("permissions", [])


def has_permission(event: dict, required_permission: str) -> bool:
    """
    Check if the request has a specific permission
    
    Args:
        event: Lambda event dict
        required_permission: Permission string like 'resource.action'
        
    Returns:
        True if permission exists, False otherwise
    """
    try:
        permissions = get_permissions_from_event(event)
        return required_permission in permissions
    except:
        return False


def require_permissions(required_permissions: Union[str, List[str]], require_all: bool = False):
    """
    Middleware factory to authorize Lambda handlers based on permissions.
    Compatible with router.attach() as the third parameter.
    
    Args:
        required_permissions: Single permission string or list of permissions
        require_all: If True, all permissions required. If False, any one is enough.
        
    Returns:
        Middleware function (event, context) -> None | raises AuthError
        
    Usage with router.attach():
        @router.attach("/admin/roles", "delete", require_permissions('role_management.delete'))
        def delete_role(event, context):
            ...
            
        @router.attach("/admin/users", "put", require_permissions(['user_management.update']))
        def update_user(event, context):
            ...
            
        @router.attach("/admin/config", "post", require_permissions(['admin.read', 'admin.write'], require_all=True))
        def update_config(event, context):
            ...
    """
    def middleware(event, context):
        try:
            permissions = get_permissions_from_event(event)
        except AuthError:
            raise AuthError(
                error_code="Unauthorised",
                error_message="Missing or invalid permissions token"
            )
        
        # Normalize to list
        required = [required_permissions] if isinstance(required_permissions, str) else required_permissions
        
        if require_all:
            # All permissions must be present
            has_access = all(perm in permissions for perm in required)
        else:
            # At least one permission must be present
            has_access = any(perm in permissions for perm in required)
        
        if not has_access:
            raise AuthError(
                error_code="Unauthorised",
                error_message=f"User does not have required permission(s): {', '.join(required)}"
            )
        
        # Return None if authorized (same as authenticate_admin)
        return None
    
    return middleware


def check_permission(event: dict, required_permissions: Union[str, List[str]], require_all: bool = False) -> None:
    """
    Check permissions and raise AuthError if not authorized (non-decorator version)
    
    Args:
        event: Lambda event dict
        required_permissions: Single permission string or list of permissions
        require_all: If True, all permissions required. If False, any one is enough.
        
    Raises:
        AuthError: if user doesn't have required permissions
        
    Usage:
        def my_handler(event, context):
            check_permission(event, 'project_management.read')
            # ... rest of handler
    """
    try:
        permissions = get_permissions_from_event(event)
    except AuthError:
        raise AuthError(
            error_code="Unauthorised",
            error_message="Missing or invalid permissions token"
        )
    
    # Normalize to list
    required = [required_permissions] if isinstance(required_permissions, str) else required_permissions
    
    if require_all:
        has_access = all(perm in permissions for perm in required)
    else:
        has_access = any(perm in permissions for perm in required)
    
    if not has_access:
        raise AuthError(
            error_code="Unauthorised",
            error_message=f"User does not have required permission(s): {', '.join(required)}"
        )


# ============================================================================
# Cognito Group Authentication
# ============================================================================

def authenticate_admin(event, context):
    authorizer = event["requestContext"]["authorizer"]
    groups = authorizer["claims"]["cognito:groups"].split(",")

    if not ENV_COGNITO.COGNITO_ADMIN_GROUP_NAME in groups:
        raise AuthError(
            error_code="Unauthorised",
            error_message="User does not have admin access",
        )

def authenticate_manager(event, context):
    authorizer = event["requestContext"]["authorizer"]
    groups = authorizer["claims"]["cognito:groups"].split(",")

    if not (
        ENV_COGNITO.COGNITO_MANAGER_GROUP_NAME in groups
        or ENV_COGNITO.COGNITO_ADMIN_GROUP_NAME in groups
    ):
        raise AuthError(
            error_code="Unauthorised",
            error_message="User does not have management access",
        )
