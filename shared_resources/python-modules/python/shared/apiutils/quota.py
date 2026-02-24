"""
Quota middleware for sBeacon query endpoints
"""

from shared.dynamodb import Quota


def require_quota(event, context):
    """
    Middleware to check and increment user quota before processing request.
    
    Raises:
        AuthError: If user has no quota or has exceeded quota limit
    """
    from shared.apiutils.router import AuthError
    
    sub = event["requestContext"]["authorizer"]["claims"]["sub"]
    
    try:
        quota = Quota.get(sub)
        
        if not quota.user_has_quota():
            raise AuthError("QUOTA_EXCEEDED", "User has exceeded quota")
        else:
            quota.increment_quota()
    except Quota.DoesNotExist:
        raise AuthError("NO_QUOTA", "User does not have a quota")
