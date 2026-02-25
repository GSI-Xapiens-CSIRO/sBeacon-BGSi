import json
import random
import string
import traceback

import boto3
from botocore.exceptions import ClientError
from markupsafe import escape

from shared.cognitoutils import authenticate_admin, create_permissions_token, require_permissions
from shared.apiutils import BeaconError, LambdaRouter
from shared.utils.lambda_utils import ENV_COGNITO, ENV_DYNAMO
from shared.dynamodb import Quota, UsageMap
from shared.dynamodb import UserInfo
from shared.dynamodb import (
    Role,
    Permission,
    RolePermission,
    UserRole,
    create_role,
    assign_permission_to_role,
    remove_permission_from_role,
    get_role_permissions,
    list_all_roles,
    list_all_permissions,
    list_all_permissions_with_disabled,
    assign_role_to_user,
    remove_role_from_user,
    get_user_roles,
    get_users_by_role,
    get_user_permissions,
)

USER_POOL_ID = ENV_COGNITO.COGNITO_USER_POOL_ID
COGNITO_REGISTRATION_EMAIL_LAMBDA = ENV_COGNITO.COGNITO_REGISTRATION_EMAIL_LAMBDA
DYNAMO_JUPYTER_INSTANCES_TABLE = ENV_DYNAMO.DYNAMO_JUPYTER_INSTANCES_TABLE
cognito_client = boto3.client("cognito-idp")
lambda_client = boto3.client("lambda")
dynamodb_client = boto3.client("dynamodb")
sagemaker_client = boto3.client("sagemaker")
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


@router.attach("/admin/users", "post", require_permissions('admin.create'))
def add_user(event, context):
    body_dict = json.loads(event.get("body"))
    email = body_dict.get("email").lower()
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
    except cognito_client.exceptions.UsernameExistsException:
        raise BeaconError(
            error_code="UsernameExistsException",
            error_message="User already exists.",
        )
    except:
        raise BeaconError(
            error_code="BeaconErrorCreatingUser",
            error_message="Error creating user.",
        )

    try:
        # add user to groups
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

    sub = next(
        attr["Value"]
        for attr in cognito_user["User"]["Attributes"]
        if attr["Name"] == "sub"
    )
    if sub:
        res["uid"] = sub

    print(f"User {email} created successfully!")
    return res


@router.attach("/admin/users", "get", require_permissions('admin.read'))
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

    userinfo_data = UserInfo.batch_get(items=keys)
    userinfo_map = {
        userinfo.to_dict()["uid"]: userinfo.to_dict() for userinfo in userinfo_data
    }

    # Fetch user roles - query UserRole table for all users
    user_roles_map = {}
    for uid in keys:
        try:
            roles = get_user_roles(uid)
            # Since 1 user = 1 role, get first role if exists
            user_roles_map[uid] = roles[0] if roles else None
        except Exception as e:
            print(f"Error getting role for user {uid}: {e}")
            user_roles_map[uid] = None

    data = []

    for user in users:
        # get quota and user info
        uid = user["uid"]
        usage_data = dynamo_quota_map.get(uid, UsageMap().as_dict())
        userinfo_data = userinfo_map.get(
            uid,
            {
                "institutionType": "",
                "institutionName": "",
            },
        )

        user["UserInfo"] = userinfo_data
        user["Usage"] = usage_data
        user["Role"] = user_roles_map.get(uid, None)
        # get MFA
        try:
            mfa = cognito_client.admin_get_user(
                UserPoolId=USER_POOL_ID, Username=user["Username"]
            ).get("UserMFASettingList", [])
        except cognito_client.exceptions.UserNotFoundException:
            continue

        user["MFA"] = mfa
        data.append(user)

    next_pagination_token = response.get("PaginationToken", None)

    return {"users": data, "pagination_token": next_pagination_token}


@router.attach("/admin/users/{email}", "delete", require_permissions('admin.delete'))
def delete_user(event, context):
    email = event["pathParameters"]["email"]
    authorizer_email = event["requestContext"]["authorizer"]["claims"]["email"]

    username = get_username_by_email(email)
    authorizer = get_username_by_email(authorizer_email)

    if username == authorizer:
        print(
            f"Unsuccessful deletion of {email}. Administrators are unable to delete themselves."
        )
        return {"success": False, "message": "Administrators cannot delete themselves."}

    response = cognito_client.admin_get_user(
        UserPoolId=USER_POOL_ID,
        Username=username,
    )
    for attr in response["UserAttributes"]:
        if attr["Name"] == "sub":
            sub = attr["Value"]
    if not sub:
        print("User sub not found")
        return {
            "success": False,
            "message": "There was a problem retrieving the user's ID.",
        }

    response = dynamodb_client.scan(
        TableName=DYNAMO_JUPYTER_INSTANCES_TABLE,
        FilterExpression="uid = :uid",
        ExpressionAttributeValues={":uid": {"S": sub}},
    )
    notebook_responses = []
    for item in response.get("Items", []):
        notebook_name = item["instanceName"]["S"]
        notebook_id = f"{notebook_name}-{sub}"
        try:
            response = sagemaker_client.describe_notebook_instance(
                NotebookInstanceName=notebook_id
            )
            notebook_responses.append(response)
        except ClientError as e:
            if e.response["Error"]["Message"] == "RecordNotFound":
                print(f"Instance {notebook_id} not found, cleaning up DynamoDB entry.")
                dynamodb_client.delete_item(
                    TableName=DYNAMO_JUPYTER_INSTANCES_TABLE,
                    Key={
                        "instanceName": {"S": notebook_name},
                        "uid": {"S": sub},
                    },
                )
            else:
                print(f"Error retrieving instance {notebook_id}: {e}")
                return {
                    "success": False,
                    "message": "There was a problem retrieving the user's active notebook instances.",
                }
    if any(
        notebook["NotebookInstanceStatus"] == "Pending"
        for notebook in notebook_responses
    ):
        return {
            "success": False,
            "message": "Some notebook instances are still pending. Please wait for them to start before deleting the user.",
        }
    for notebook in notebook_responses:
        if notebook["NotebookInstanceStatus"] == "InService":
            try:
                sagemaker_client.stop_notebook_instance(
                    NotebookInstanceName=notebook["NotebookInstanceName"]
                )
                print(f"Stopped notebook instance {notebook['NotebookInstanceName']}")
            except ClientError as e:
                print(f"Error stopping instance {notebook_id}: {e}")
                return {
                    "success": False,
                    "message": "There was a problem stopping the user's active notebook instances.",
                }

    # delete user quota
    try:
        quota = Quota.get(sub)
        quota.delete()
    except Quota.DoesNotExist:
        print(f"Quota for user {sub} does not exist.")

    cognito_client.admin_delete_user(UserPoolId=USER_POOL_ID, Username=username)

    print(f"User with email {email} removed successfully!")
    return {"success": True}


@router.attach("/admin/users/{email}/mfa", "delete", require_permissions('admin.delete'))
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


@router.attach("/admin/users/{email}/groups", "get", require_permissions('admin.read'))
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

    return {
        "groups": groups,
        "user": username,
        "authorizer": authorizer,
    }


@router.attach("/admin/users/{email}/groups", "post", require_permissions('admin.update'))
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


# ============================================================================
# RBAC - Role Management APIs
# ============================================================================


@router.attach("/admin/roles", "get", require_permissions('admin.read'))
def get_roles(event, context):
    """
    Get all roles in the system with their permission counts
    Optional query params:
      - status: "active" | "inactive" | "all" (default: "all")
      - search: search term for role name (case-insensitive)
      - limit: number of items to return (default: 10)
      - last_evaluated_key: pagination key from previous request
    """
    try:
        query_params = event.get("queryStringParameters") or {}
        status_filter = query_params.get("status", "all").lower()
        search_term = query_params.get("search", None)
        limit = int(query_params.get("limit", 10))
        last_evaluated_key = query_params.get("last_evaluated_key", None)

        # Parse last_evaluated_key if provided
        if last_evaluated_key:
            last_evaluated_key = json.loads(last_evaluated_key)

        # Set status filter for helper function
        status = None if status_filter == "all" else status_filter

        # Get roles with pagination
        roles, next_key = list_all_roles(
            limit=limit,
            last_evaluated_key=last_evaluated_key,
            search_term=search_term,
            status_filter=status
        )

        # Enrich with permission count and user count
        for role in roles:
            role_id = role["role_id"]
            try:
                permissions = get_role_permissions(role_id)
                role["permission_count"] = len(permissions)
            except Exception as e:
                print(f"Error getting permissions for role {role_id}: {e}")
                role["permission_count"] = 0

            try:
                users = get_users_by_role(role_id)
                role["user_count"] = len(users)
            except Exception as e:
                print(f"Error getting users for role {role_id}: {e}")
                role["user_count"] = 0

            role["status"] = "Active" if role.get("is_active", True) else "Inactive"

        # Format last_evaluated_key for response
        formatted_key = json.dumps(next_key) if next_key else None

        return {
            "success": True,
            "roles": roles,
            "total": len(roles),
            "last_evaluated_key": formatted_key
        }
    except Exception as e:
        print(f"Error getting roles: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "message": "Error retrieving roles from database."
        }


@router.attach("/admin/roles/{role_id}", "get", require_permissions('admin.read'))
def get_role_details(event, context):
    """
    Get detailed information about a specific role including all permissions
    """
    role_id = event["pathParameters"]["role_id"]

    try:
        role = Role.get(role_id)
        role_dict = role.to_dict()

        # Get all permissions for this role
        permissions = get_role_permissions(role_id)

        # Get all users with this role
        users = get_users_by_role(role_id)

        role_dict["permissions"] = permissions
        role_dict["users"] = users
        role_dict["permission_count"] = len(permissions)
        role_dict["user_count"] = len(users)
        role_dict["status"] = "Active" if role_dict.get("is_active", True) else "Inactive"

        return {
            "success": True,
            "role": role_dict
        }
    except Role.DoesNotExist:
        raise BeaconError(
            error_code="RoleNotFound",
            error_message=f"Role with ID {role_id} not found."
        )
    except Exception as e:
        print(f"Error getting role details: {e}")
        raise BeaconError(
            error_code="BeaconErrorGettingRoleDetails",
            error_message="Error retrieving role details."
        )


@router.attach("/admin/roles", "post", require_permissions('admin.create'))
def create_new_role(event, context):
    """
    Create a new role with specified permissions

    Body:
    {
        "role_name": "Data Manager",
        "is_active": true,
        "permissions": ["project_onboarding.read", "project_onboarding.create", ...]
    }
    """
    body_dict = json.loads(event.get("body"))
    role_name = body_dict.get("role_name")
    description = body_dict.get("description", "")
    is_active = body_dict.get("is_active", True)
    permissions = body_dict.get("permissions", [])

    if not role_name:
        return {
            "success": False,
            "message": "Role name is required."
        }

    try:
        # Check if role name already exists
        existing_roles, _ = list_all_roles()
        for existing_role in existing_roles:
            if existing_role.get('role_name', '').lower() == role_name.lower():
                return {
                    "success": False,
                    "message": f"Role name '{role_name}' already exists. Please use a different name."
                }

        # Create the role
        role_id = create_role(role_name, description, is_active)

        if not role_id:
            return {
                "success": False,
                "message": "Failed to create role in database."
            }

        # Assign permissions to the role
        failed_permissions = []
        for permission_id in permissions:
            if not assign_permission_to_role(role_id, permission_id):
                failed_permissions.append(permission_id)

        if failed_permissions:
            print(f"Failed to assign permissions: {failed_permissions}")

        print(f"Role {role_name} created successfully with ID {role_id}")

        return {
            "success": True,
            "message": f"Role '{role_name}' created successfully.",
            "role_id": role_id,
            "role_name": role_name,
            "is_active": is_active,
            "permissions_assigned": len(permissions) - len(failed_permissions),
            "permissions_failed": len(failed_permissions)
        }
    except Exception as e:
        print(f"Error creating role: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "message": "Error creating role in database."
        }


@router.attach("/admin/roles/{role_id}", "put", require_permissions('admin.update'))
def update_role(event, context):
    """
    Update role details and permissions

    Body:
    {
        "role_name": "Data Manager",
        "description": "...",
        "is_active": true,
        "permissions": ["project_onboarding.read", ...]  // Complete list
    }
    """
    role_id = event["pathParameters"]["role_id"]
    body_dict = json.loads(event.get("body"))

    try:
        # Get existing role
        role = Role.get(role_id)

        # Check if role_name is being changed and if it already exists
        if "role_name" in body_dict:
            new_role_name = body_dict["role_name"]
            if new_role_name.lower() != role.role_name.lower():
                existing_roles, _ = list_all_roles()
                for existing_role in existing_roles:
                    if existing_role.get('role_id') != role_id and existing_role.get('role_name', '').lower() == new_role_name.lower():
                        return {
                            "success": False,
                            "message": f"Role name '{new_role_name}' already exists. Please use a different name."
                        }
            role.role_name = new_role_name
            role.role_name_lower = new_role_name.lower()

        # Update basic info if provided
        if "description" in body_dict:
            role.description = body_dict["description"]
        if "is_active" in body_dict:
            role.is_active = body_dict["is_active"]

        role.save()

        # Update permissions if provided
        if "permissions" in body_dict:
            new_permissions = set(body_dict["permissions"])
            current_permissions = set(get_role_permissions(role_id))

            # Remove permissions that are no longer needed
            permissions_to_remove = current_permissions - new_permissions
            for permission_id in permissions_to_remove:
                remove_permission_from_role(role_id, permission_id)

            # Add new permissions
            permissions_to_add = new_permissions - current_permissions
            for permission_id in permissions_to_add:
                assign_permission_to_role(role_id, permission_id)

            print(f"Role {role_id} updated: +{len(permissions_to_add)} -{len(permissions_to_remove)} permissions")

        return {
            "success": True,
            "message": "Role updated successfully.",
            "role_id": role_id
        }
    except Role.DoesNotExist:
        return {
            "success": False,
            "message": f"Role with ID {role_id} not found."
        }
    except Exception as e:
        print(f"Error updating role: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "message": "Error updating role in database."
        }


@router.attach("/admin/roles/{role_id}", "delete", require_permissions('admin.delete'))
def delete_role(event, context):
    """
    Delete a role (removes all user assignments and permissions)
    """
    role_id = event["pathParameters"]["role_id"]

    try:
        # Check if role exists
        role = Role.get(role_id)
        role_name = role.role_name

        # Get users with this role
        users_with_role = get_users_by_role(role_id)

        if users_with_role:
            # Remove role from all users
            for uid in users_with_role:
                remove_role_from_user(uid, role_id)
            print(f"Removed role from {len(users_with_role)} users")

        # Remove all permissions from role
        permissions = get_role_permissions(role_id)
        for permission_id in permissions:
            remove_permission_from_role(role_id, permission_id)

        # Delete the role
        role.delete()

        print(f"Role {role_name} ({role_id}) deleted successfully")

        return {
            "success": True,
            "message": f"Role '{role_name}' deleted successfully.",
            "users_affected": len(users_with_role)
        }
    except Role.DoesNotExist:
        return {
            "success": False,
            "message": f"Role with ID {role_id} not found."
        }
    except Exception as e:
        print(f"Error deleting role: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "message": "Error deleting role from database."
        }


@router.attach("/admin/roles/{role_id}/users", "get", require_permissions('admin.read'))
def get_role_users(event, context):
    """
    Get all users assigned to a specific role
    """
    role_id = event["pathParameters"]["role_id"]

    try:
        # Verify role exists
        role = Role.get(role_id)

        # Get user IDs
        user_ids = get_users_by_role(role_id)

        # Enrich with user details from Cognito
        users = []
        for uid in user_ids:
            try:
                # Query Cognito for user details
                response = cognito_client.list_users(
                    UserPoolId=USER_POOL_ID,
                    Filter=f'sub = "{uid}"',
                    Limit=1
                )

                if response.get("Users"):
                    user = response["Users"][0]
                    users.append({
                        "uid": uid,
                        "username": user.get("Username"),
                        "email": next((attr["Value"] for attr in user.get("Attributes", [])
                                      if attr["Name"] == "email"), None),
                        "first_name": next((attr["Value"] for attr in user.get("Attributes", [])
                                           if attr["Name"] == "given_name"), None),
                        "last_name": next((attr["Value"] for attr in user.get("Attributes", [])
                                          if attr["Name"] == "family_name"), None),
                    })
            except Exception as e:
                print(f"Error getting user details for {uid}: {e}")
                users.append({"uid": uid, "error": "User details not found"})

        return {
            "success": True,
            "role_id": role_id,
            "role_name": role.role_name,
            "users": users,
            "total": len(users)
        }
    except Role.DoesNotExist:
        raise BeaconError(
            error_code="RoleNotFound",
            error_message=f"Role with ID {role_id} not found."
        )
    except Exception as e:
        print(f"Error getting role users: {e}")
        raise BeaconError(
            error_code="BeaconErrorGettingRoleUsers",
            error_message="Error retrieving users for role."
        )


@router.attach("/admin/permissions", "get", require_permissions('admin.read'))
def get_all_permissions(event, context):
    """
    Get all available permissions in the system
    Returns organized by resource and action
    """
    try:
        permissions = list_all_permissions()

        # Organize permissions by resource
        organized = {}
        for perm_id in permissions:
            if "." in perm_id:
                resource, action = perm_id.split(".", 1)
                if resource not in organized:
                    organized[resource] = []
                organized[resource].append(action)

        return {
            "success": True,
            "permissions": permissions,
            "organized": organized,
            "total": len(permissions)
        }
    except Exception as e:
        print(f"Error getting permissions: {e}")
        raise BeaconError(
            error_code="BeaconErrorGettingPermissions",
            error_message="Error retrieving permissions from database."
        )


@router.attach("/admin/permissions/matrix", "get", require_permissions('admin.read'))
def get_permissions_matrix(event, context):
    """
    Get permissions formatted as a matrix for UI checkboxes
    Returns structure suitable for rendering permission table
    
    Matrix shows all possible action combinations, with disabled flag for invalid ones.
    Valid permissions are seeded from Terraform config (dynamodb.tf)

    Returns:
    {
      "actions": ["create", "read", "update", "delete", "download"],
      "resources": [
        {
          "name": "project_onboarding",
          "label": "Project Onboarding",
          "permissions": {
            "create": {"id": "project_onboarding.create", "disabled": false, "exists": true},
            "read": {"id": "project_onboarding.read", "disabled": true, "exists": false},
            ...
          }
        }
      ]
    }
    """
    try:
        # Get all permissions from database (includes disabled flag from Terraform)
        all_permissions = list_all_permissions_with_disabled()

        # Define standard actions
        standard_actions = ["create", "read", "update", "delete", "download"]

        # Group permissions by resource
        resources_map = {}
        for perm in all_permissions:
            perm_id = perm["permission_id"]
            disabled = perm.get("disabled", False)
            
            if "." in perm_id:
                resource, action = perm_id.split(".", 1)
                if resource not in resources_map:
                    resources_map[resource] = {}
                
                resources_map[resource][action] = {
                    "id": perm_id,
                    "disabled": disabled,
                    "exists": not disabled  # Only non-disabled permissions are assignable
                }

        # Build matrix for all resources
        resources = []
        for resource_name in sorted(resources_map.keys()):
            # Create permission object for each standard action
            permissions_obj = resources_map[resource_name]
            
            resources.append({
                "name": resource_name,
                "label": resource_name.replace("_", " ").title(),
                "permissions": permissions_obj
            })

        return {
            "success": True,
            "actions": standard_actions,
            "resources": resources,
            "total_resources": len(resources),
            "total_permissions": len(all_permissions)
        }
    except Exception as e:
        print(f"Error getting permissions matrix: {e}")
        raise BeaconError(
            error_code="BeaconErrorGettingPermissionsMatrix",
            error_message="Error retrieving permissions matrix."
        )


# ============================================================================
# RBAC - User Role Assignment APIs
# ============================================================================


@router.attach("/admin/users/{uid}/roles", "get", require_permissions('admin.read'))
def get_user_role_assignments(event, context):
    """
    Get all roles assigned to a specific user
    """
    uid = event["pathParameters"]["uid"]

    try:
        roles = get_user_roles(uid)

        return {
            "success": True,
            "uid": uid,
            "roles": roles,
            "total": len(roles)
        }
    except Exception as e:
        print(f"Error getting user roles: {e}")
        raise BeaconError(
            error_code="BeaconErrorGettingUserRoles",
            error_message="Error retrieving user roles from database."
        )


@router.attach("/admin/users/{uid}/roles", "post", require_permissions('admin.create'))
def assign_user_role(event, context):
    """
    Assign a role to a user

    Body:
    {
        "role_id": "uuid-of-role"
    }
    """
    uid = event["pathParameters"]["uid"]
    body_dict = json.loads(event.get("body"))
    role_id = body_dict.get("role_id")

    if not role_id:
        raise BeaconError(
            error_code="BeaconMissingRoleId",
            error_message="Role ID is required."
        )

    try:
        # Verify role exists
        role = Role.get(role_id)

        # Assign role to user
        success = assign_role_to_user(uid, role_id)

        if success:
            print(f"Role {role.role_name} assigned to user {uid}")
            return {
                "success": True,
                "message": f"Role {role.role_name} assigned successfully"
            }
        else:
            raise Exception("Failed to assign role")
    except Role.DoesNotExist:
        raise BeaconError(
            error_code="RoleNotFound",
            error_message=f"Role with ID {role_id} not found."
        )
    except Exception as e:
        print(f"Error assigning role to user: {e}")
        raise BeaconError(
            error_code="BeaconErrorAssigningRole",
            error_message="Error assigning role to user."
        )


@router.attach("/admin/users/{uid}/roles", "put", require_permissions('admin.update'))
def set_user_role(event, context):
    """
    Set/replace user's role (1 user = 1 role)
    Removes existing role and assigns new one

    Body:
    {
        "role_id": "uuid-of-role"
    }
    """
    uid = event["pathParameters"]["uid"]
    body_dict = json.loads(event.get("body"))
    new_role_id = body_dict.get("role_id")

    if not new_role_id:
        raise BeaconError(
            error_code="BeaconMissingRoleId",
            error_message="Role ID is required."
        )

    try:
        # Verify new role exists and is active
        new_role = Role.get(new_role_id)
        if not new_role.is_active:
            raise BeaconError(
                error_code="RoleNotActive",
                error_message=f"Role {new_role.role_name} is not active."
            )

        # Get current roles and remove them
        current_roles = get_user_roles(uid)
        for role_data in current_roles:
            remove_role_from_user(uid, role_data["role_id"])

        # Assign new role
        success = assign_role_to_user(uid, new_role_id)

        if success:
            print(f"Role {new_role.role_name} set for user {uid}")
            return {
                "success": True,
                "message": f"Role {new_role.role_name} assigned successfully",
                "role": new_role.to_dict()
            }
        else:
            raise Exception("Failed to assign role")
    except Role.DoesNotExist:
        raise BeaconError(
            error_code="RoleNotFound",
            error_message=f"Role with ID {new_role_id} not found."
        )
    except BeaconError:
        raise
    except Exception as e:
        print(f"Error setting user role: {e}")
        raise BeaconError(
            error_code="BeaconErrorSettingRole",
            error_message="Error setting user role."
        )


@router.attach("/admin/users/permissions", "get")
def get_user_permissions_endpoint(event, context):
    """
    Get all permissions for a specific user, returned as a JWT
    """
    uid = event["requestContext"]["authorizer"]["claims"]["sub"]

    try:
        permissions = get_user_permissions(uid)
        
        # Create Payload
        payload = {
            "sub": uid,
            "permissions": permissions
        }
        
        token = create_permissions_token(payload)
        
        return {
            "success": True,
            "token": token
        }
    except Exception as e:
        print(f"Error getting user permissions: {e}")
        raise BeaconError(
            error_code="BeaconErrorGettingUserPermissions",
            error_message="Error retrieving user permissions."
        )
