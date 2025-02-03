import os

from utils.cognito import search_users_from_attribute, get_user_attribute
from shared.cognitoutils import authenticate_manager
from shared.apiutils import LambdaRouter, PortalError


router = LambdaRouter()
DPORTAL_BUCKET = os.environ.get("DPORTAL_BUCKET")
ATHENA_METADATA_BUCKET = os.environ.get("ATHENA_METADATA_BUCKET")
SUBMIT_LAMBDA = os.environ.get("SUBMIT_LAMBDA")
INDEXER_LAMBDA = os.environ.get("INDEXER_LAMBDA")


#
# Files' User Functions
#
@router.attach("/dportal/admin/users", "get", authenticate_manager)
def search_users(event, context):
    query_params = event.get("queryStringParameters", {})
    search = query_params.get("search", "")

    if len(search) < 3:
        return []

    try:
        users = search_users_from_attribute("email", search)
        users = [
            {
                "firstName": get_user_attribute(user, "given_name"),
                "lastName": get_user_attribute(user, "family_name"),
                "email": get_user_attribute(user, "email"),
            }
            for user in users
        ]

        return users
    except PortalError as e:
        return []
