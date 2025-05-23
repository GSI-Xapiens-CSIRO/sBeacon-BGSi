from shared.utils import ENV_COGNITO
from shared.apiutils import AuthError


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
