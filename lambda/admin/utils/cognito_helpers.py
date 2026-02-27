"""
Cognito Helper Functions
"""

import boto3
from shared.utils.lambda_utils import ENV_COGNITO

USER_POOL_ID = ENV_COGNITO.COGNITO_USER_POOL_ID
cognito_client = boto3.client("cognito-idp")


def get_username_by_email(email):
    """
    Get Cognito username by email address
    
    Args:
        email: User email address
        
    Returns:
        Username string
        
    Raises:
        Exception if user not found
    """
    response = cognito_client.list_users(
        UserPoolId=USER_POOL_ID, Filter=f'email = "{email}"', Limit=1
    )

    if response.get("Users"):
        return response["Users"][0]["Username"]

    raise Exception(f"User with email {email} not found")


def logout_all_sessions(email):
    """
    Sign out user from all active sessions
    
    Args:
        email: User email address
    """
    username = get_username_by_email(email)
    cognito_client.admin_user_global_sign_out(
        UserPoolId=USER_POOL_ID, Username=username
    )
