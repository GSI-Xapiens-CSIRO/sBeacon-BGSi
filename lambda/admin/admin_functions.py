import json
import random
import string

import boto3
from markupsafe import escape

from admin_utils import authenticate_admin
from shared.apiutils import BeaconError, LambdaRouter
from shared.utils.lambda_utils import ENV_COGNITO, ENV_BEACON, ENV_SES

USER_POOL_ID = ENV_COGNITO.COGNITO_USER_POOL_ID
BEACON_UI_URL = ENV_BEACON.BEACON_UI_URL
SES_SOURCE_EMAIL = ENV_SES.SES_SOURCE_EMAIL
SES_CONFIG_SET_NAME = ENV_SES.SES_CONFIG_SET_NAME
cognito_client = boto3.client("cognito-idp")
ses_client = boto3.client("ses")
router = LambdaRouter()


def get_username_by_email(email):
    response = cognito_client.list_users(
        UserPoolId=USER_POOL_ID, Filter=f'email = "{email}"', Limit=1
    )

    if response.get("Users"):
        return response["Users"][0]["Username"]

    raise Exception(f"User with email {email} not found")


@router.attach("/admin/users", "post", authenticate_admin)
def add_user(event, context):
    body_dict = json.loads(event.get("body"))
    email = body_dict.get("email")
    first_name = body_dict.get("first_name")
    last_name = body_dict.get("last_name")

    if not all([email, first_name, last_name]):
        raise BeaconError(
            error_code="BeaconAddUserMissingAttribute",
            error_message="Missing required attributes!",
        )

    temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))

    cognito_client.admin_create_user(
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

    beacon_ui_url = f"{BEACON_UI_URL}/login"
    beacon_img_url = f"{BEACON_UI_URL}/assets/images/sbeacon.png" # There are likely better ways of doing this, but email template is not important for now

    subject = "sBeacon Registration"
    body_html = f"""
    <html>
      <head>
        <style>
          body {{
            font-family: Arial, sans-serif;
            color: #333;
          }}
          .container {{
            max-width: 600px;
            margin: auto;
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 5px;
            background-color: #f9f9f9;
          }}
          h1 {{
            color: #33548e;
          }}
          p {{
            line-height: 1.6;
          }}
        </style>
      </head>
      <body>
        <div class="container">
          <h1>Hello {escape(first_name)} {escape(last_name)},</h1>
          <p>Welcome to sBeacon - your sign-in credentials are as follows:</p>
          <p>Email: <strong>{escape(email)}</strong></p>
          <p>Temporary Password: <strong>{temp_password}</strong></p>
          <p><a href="{beacon_ui_url}">Access your account</a></p>
          <div style="max-width:80;">
            <img src="{beacon_img_url}" alt="sBeacon Logo" style="max-width:80%; width:80%; margin-top:20px;">
          </div>
        </div>
      </body>
    </html>
    """

    response = ses_client.send_email(
        Destination={
            'ToAddresses': [email],
        },
        Message={
            'Body': 
            {
                'Html': {
                    'Charset': 'UTF-8',
                    'Data': body_html,
                },
                'Text': {
                    'Charset': 'UTF-8',
                    'Data': f"Hello {first_name} {last_name},\n\nWelcome to sBeacon - your sign-in credentials are as follows:\n\nEmail: {email}\n\nPassword: {temp_password}\n\nVerify: {beacon_ui_url}",
                }
            },
            'Subject': {
                'Charset': 'UTF-8',
                'Data': subject,
            },
        },
        Source=SES_SOURCE_EMAIL,
        ReturnPath=SES_SOURCE_EMAIL,
        ConfigurationSetName=SES_CONFIG_SET_NAME
    )

    print(f"User {email} created successfully!")
    print(f"Email sent with message ID: {response["MessageId"]}")
    return {"success": True}


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
    next_pagination_token = response.get("PaginationToken", None)

    return {"users": users, "pagination_token": next_pagination_token}


@router.attach("/admin/users/{email}", "delete", authenticate_admin)
def delete_user(event, context):
    email = event["pathParameters"]["email"]
    authorizer_email = event["requestContext"]["authorizer"]["claims"]["email"]

    username = get_username_by_email(email)
    authorizer = get_username_by_email(authorizer_email)

    if username == authorizer:
        print(f"Unsuccessful deletion of {email}. Administrators are unable to delete themselves.")
        return {"success": False}

    cognito_client.admin_delete_user(UserPoolId=USER_POOL_ID, Username=username)

    print(f"User with email {email} removed successfully!")
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

    if body_dict["groups"]["admin"]:
        chosen_groups.append("administrators")
    else:
        removed_groups.append("administrators")
    if body_dict["groups"]["record"]:
        chosen_groups.append("record-access-user-group")
    else:
        removed_groups.append("record-access-user-group")
    if body_dict["groups"]["count"]:
        chosen_groups.append("count-access-user-group")
    else:
        removed_groups.append("count-access-user-group")
    if body_dict["groups"]["boolean"]:
        chosen_groups.append("boolean-access-user-group")
    else:
        removed_groups.append("boolean-access-user-group")

    username = get_username_by_email(email)
    authorizer = get_username_by_email(authorizer_email)
    
    if username == authorizer and "administrators" in removed_groups:
        print(f"Unsuccessful. Administrators are unable to decrease their own permissions.")
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
    return {"success": True}
