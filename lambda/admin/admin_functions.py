import json
import random
import string

import boto3
from markupsafe import escape

from shared.cognitoutils import authenticate_admin
from shared.apiutils import BeaconError, LambdaRouter
from shared.utils.lambda_utils import ENV_COGNITO
from shared.dynamodb import Quota, UsageMap

USER_POOL_ID = ENV_COGNITO.COGNITO_USER_POOL_ID
COGNITO_REGISTRATION_EMAIL_LAMBDA = ENV_COGNITO.COGNITO_REGISTRATION_EMAIL_LAMBDA
cognito_client = boto3.client("cognito-idp")
lambda_client = boto3.client("lambda")
router = LambdaRouter()


def get_username_by_email(email):
    response = cognito_client.list_users(
        UserPoolId=USER_POOL_ID, Filter=f'email = "{email}"', Limit=1
    )

    if response.get("Users"):
        return response["Users"][0]["Username"]

    raise Exception(f"User with email {email} not found")


def logout_all_sessions(email):
    username = get_username_by_email(email)
    cognito_client.admin_user_global_sign_out(
        UserPoolId=USER_POOL_ID, Username=username
    )


@router.attach("/admin/users", "post", authenticate_admin)
def add_user(event, context):
    body_dict = json.loads(event.get("body"))
    email = body_dict.get("email")
    first_name = body_dict.get("first_name")
    last_name = body_dict.get("last_name")
    groups = body_dict.get("groups")

    if not all([email, first_name, last_name, groups]):
        raise BeaconError(
            error_code="BeaconAddUserMissingAttribute",
            error_message="Missing required attributes!",
        )

    lower_case = random.choices(string.ascii_lowercase, k=2)
    upper_case = random.choices(string.ascii_uppercase, k=2)
    digits = random.choices(string.digits, k=2)
    special = random.choices(string.punctuation, k=2)

    characters = lower_case + upper_case + digits + special
    random.shuffle(characters)
    temp_password = "".join(characters)

    try:
        cognito_user = cognito_client.admin_create_user(
            UserPoolId=USER_POOL_ID,
            Username=email,
            TemporaryPassword=temp_password,
            MessageAction="SUPPRESS",
            UserAttributes=[
                {"Name": "email", "Value": email},
                {"Name": "given_name", "Value": first_name},
                {"Name": "family_name", "Value": last_name},
                {"Name": "email_verified", "Value": "true"},
            ],
        )
    except:
        raise BeaconError(
            error_code="BeaconErrorCreatingUser",
            error_message="Error creating user.",
        )

    try:
        for group_name, chosen in groups.items():
            if chosen:
                cognito_client.admin_add_user_to_group(
                    UserPoolId=USER_POOL_ID, Username=email, GroupName=group_name
                )
    except:
        cognito_client.admin_delete_user(
            UserPoolId=USER_POOL_ID,
            Username=email,
        )
        raise BeaconError(
            error_code="BeaconErrorAddingUserToGroups",
            error_message="Error adding user to the requested groups.",
        )

    try:
        payload = {
            "body": {
                "email": email,
                "temporary_password": temp_password,
                "first_name": first_name,
                "last_name": last_name,
            }
        }
        response = lambda_client.invoke(
            FunctionName=COGNITO_REGISTRATION_EMAIL_LAMBDA,
            InvocationType="RequestResponse",
            Payload=json.dumps(payload),
        )
        if not (payload_stream := response.get("Payload")):
            raise Exception("Error invoking email Lambda: No response payload")
        body = json.loads(payload_stream.read().decode("utf-8"))
        if not body.get("success", False):
            raise Exception(f"Error invoking email Lambda: {body.get('message')}")
    except:
        cognito_client.admin_delete_user(
            UserPoolId=USER_POOL_ID,
            Username=email,
        )
        raise BeaconError(
            error_code="BeaconRegistrationEmailFailed",
            error_message="The registration email failed to send.",
        )

    res = {"success": True}

    user_sub = next(
        attr["Value"]
        for attr in cognito_user["User"]["Attributes"]
        if attr["Name"] == "sub"
    )
    if user_sub:
        res["uid"] = user_sub

    print(f"User {email} created successfully!")
    return res


@router.attach("/admin/users", "get", authenticate_admin)
def get_users(event, context):
    pagination_token = (event.get("queryStringParameters") or dict()).get(
        "pagination_token", None
    )
    limit = int((event.get("queryStringParameters") or dict()).get("limit", 60))
    filterKey = (event.get("queryStringParameters") or dict()).get("key", None)
    filterValue = (event.get("queryStringParameters") or dict()).get("query", None)
    kwargs = {
        "UserPoolId": USER_POOL_ID,
        "Limit": limit,
    }
    if pagination_token:
        kwargs["PaginationToken"] = pagination_token
    if filterKey and filterValue:
        kwargs["Filter"] = f'{filterKey} ^= "{filterValue}"'

    response = cognito_client.list_users(**kwargs)
    # Extract users and next pagination token
    users = response.get("Users", [])

    keys = []
    for user in users:
        user_id = next(
            attr["Value"] for attr in user["Attributes"] if attr["Name"] == "sub"
        )
        user["uid"] = user_id
        keys.append(user_id)

    quota_data = Quota.batch_get(items=keys)
    dynamo_quota_map = {
        quota.to_dict()["uid"]: quota.to_dict()["Usage"] for quota in quota_data
    }
    data = []

    for user in users:
        # get quota
        uid = user["uid"]
        usage_data = dynamo_quota_map.get(uid, UsageMap().as_dict())
        user["Usage"] = usage_data
        # get MFA
        mfa = cognito_client.admin_get_user(
            UserPoolId=USER_POOL_ID, Username=user["Username"]
        ).get("UserMFASettingList", [])
        user["MFA"] = mfa
        data.append(user)

    next_pagination_token = response.get("PaginationToken", None)

    return {"users": data, "pagination_token": next_pagination_token}


@router.attach("/admin/users/{email}", "delete", authenticate_admin)
def delete_user(event, context):
    email = event["pathParameters"]["email"]
    authorizer_email = event["requestContext"]["authorizer"]["claims"]["email"]

    username = get_username_by_email(email)
    authorizer = get_username_by_email(authorizer_email)

    if username == authorizer:
        print(
            f"Unsuccessful deletion of {email}. Administrators are unable to delete themselves."
        )
        return {"success": False}

    cognito_client.admin_delete_user(UserPoolId=USER_POOL_ID, Username=username)

    print(f"User with email {email} removed successfully!")
    return {"success": True}


@router.attach("/admin/users/{email}/mfa", "delete", authenticate_admin)
def clear_user_mfa(event, context):
    email = event["pathParameters"]["email"]
    authorizer_email = event["requestContext"]["authorizer"]["claims"]["email"]

    authorizer = get_username_by_email(authorizer_email)
    username = get_username_by_email(email)

    if username == authorizer:
        print(
            f"Unable to clear MFA for {email}. Administrators are unable to deactivate their MFA."
        )
        return {"success": False}

    cognito_client.admin_set_user_mfa_preference(
        UserPoolId=USER_POOL_ID,
        Username=username,
        SMSMfaSettings={"Enabled": False, "PreferredMfa": False},
        SoftwareTokenMfaSettings={"Enabled": False, "PreferredMfa": False},
    )

    print(f"User with email {email} got their MFA deactivated successfully!")
    return {"success": True}


@router.attach("/admin/users/{email}/groups", "get", authenticate_admin)
def user_groups(event, context):
    email = event["pathParameters"]["email"]
    authorizer_email = event["requestContext"]["authorizer"]["claims"]["email"]
    username = get_username_by_email(email)
    authorizer = get_username_by_email(authorizer_email)
    response = cognito_client.admin_list_groups_for_user(
        Username=username, UserPoolId=USER_POOL_ID
    )

    groups = response.get("Groups", [])
    print(f"User with email {email} has {len(groups)} groups")
    return {"groups": groups, "user": username, "authorizer": authorizer}


@router.attach("/admin/users/{email}/groups", "post", authenticate_admin)
def update_user_groups(event, context):
    email = event["pathParameters"]["email"]
    authorizer_email = event["requestContext"]["authorizer"]["claims"]["email"]
    body_dict = json.loads(event.get("body"))
    chosen_groups = []
    removed_groups = []

    # changed group associations
    for group, chosen in body_dict["groups"].items():
        if chosen:
            chosen_groups.append(group)
        else:
            removed_groups.append(group)

    username = get_username_by_email(email)
    authorizer = get_username_by_email(authorizer_email)

    # admin cannot remove themself from administrators group
    if username == authorizer and "administrators" in removed_groups:
        print(
            f"Unsuccessful. Administrators are unable to decrease their own permissions."
        )
        return {"success": False}

    for group_name in chosen_groups:
        cognito_client.admin_add_user_to_group(
            UserPoolId=USER_POOL_ID, Username=username, GroupName=group_name
        )

    for group_name in removed_groups:
        cognito_client.admin_remove_user_from_group(
            UserPoolId=USER_POOL_ID, Username=username, GroupName=group_name
        )

    print(
        f"User with email {email} added to {len(chosen_groups)} and removed from {len(removed_groups)} groups"
    )

    logout_all_sessions(email)
    return {"success": True}
