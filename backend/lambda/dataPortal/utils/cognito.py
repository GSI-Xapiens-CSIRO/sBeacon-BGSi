import boto3
import os
from functools import lru_cache

from .router import PortalError

cognito_client = boto3.client("cognito-idp")
USER_POOL_ID = os.environ.get("USER_POOL_ID")


@lru_cache(maxsize=128)
def get_user_from_attribute(attribute, value):
    try:
        response = cognito_client.list_users(
            UserPoolId=USER_POOL_ID, Filter=f'{attribute} = "{value}"'
        )
        users = response.get("Users", [])
        if not users:
            raise PortalError(404, "User not found")
        return users[0]
    except cognito_client.exceptions.UserNotFoundException:
        raise PortalError(404, "User not found")
    except Exception as e:
        raise PortalError(500, str(e))


def get_user_attribute(user, attribute_name):
    for attribute in user["Attributes"]:
        if attribute["Name"] == attribute_name:
            return attribute["Value"]
    raise PortalError(404, f"{attribute_name} attribute not found")
