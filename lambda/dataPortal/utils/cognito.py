import boto3
import os
from functools import lru_cache

from shared.apiutils import PortalError

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
            raise PortalError(404, f"User {attribute}:{value} not found")
        return users[0]
    except cognito_client.exceptions.UserNotFoundException:
        raise PortalError(404, f"User {attribute}:{value} not found")
    except PortalError as e:
        raise e
    except Exception as e:
        raise PortalError(500, str(e))


def search_users_from_attribute(attribute, value):
    try:
        response = cognito_client.list_users(
            UserPoolId=USER_POOL_ID, Filter=f'{attribute} ^= "{value}"', Limit=10
        )
        users = response.get("Users", [])
        if not users:
            raise PortalError(404, "User not found")
        return users
    except cognito_client.exceptions.UserNotFoundException:
        raise PortalError(404, "User not found")
    except PortalError as e:
        raise e
    except Exception as e:
        raise PortalError(500, str(e))


def get_user_attribute(user, attribute_name):
    for attribute in user["Attributes"]:
        if attribute["Name"] == attribute_name:
            return attribute["Value"]
    return "NULL"


def list_users():
    users = []
    pagination_token = None

    while True:
        if pagination_token:
            response = cognito_client.list_users(
                UserPoolId=USER_POOL_ID, PaginationToken=pagination_token
            )
        else:
            response = cognito_client.list_users(UserPoolId=USER_POOL_ID)

        users.extend(response.get("Users", []))
        pagination_token = response.get("PaginationToken")

        if not pagination_token:
            break
    users = [
        {attr["Name"]: attr["Value"] for attr in user["Attributes"]} for user in users
    ]
    return users
