import json
import os

from utils.router import LambdaRouter, PortalError
from utils.models import Projects, ProjectUsers
from utils.s3_util import list_s3_prefix, delete_s3_objects
import boto3
from pynamodb.exceptions import DoesNotExist

router = LambdaRouter()
cognito_client = boto3.client("cognito-idp")
USER_POOL_ID = os.environ.get("USER_POOL_ID")
DPORTAL_BUCKET = os.environ.get("DPORTAL_BUCKET")


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


#
# Project User Functions
#


@router.attach("/dportal/admin/projects/{name}/users", "get")
def list_project_users(event, context):
    name = event["pathParameters"]["name"]

    try:
        Projects.get(name)
    except DoesNotExist:
        raise PortalError(404, "Project not found")

    user_projects = ProjectUsers.query(name)
    users = [
        get_user_from_attribute("sub", user_project.uid)
        for user_project in user_projects
    ]
    users = [
        {
            "firstName": get_user_attribute(user, "given_name"),
            "lastName": get_user_attribute(user, "family_name"),
            "email": get_user_attribute(user, "email"),
        }
        for user in users
    ]

    return users


@router.attach("/dportal/admin/projects/{name}/users/{email}", "delete")
def remove_project_user(event, context):
    name = event["pathParameters"]["name"]
    email = event["pathParameters"]["email"]
    user = get_user_from_attribute("email", email)
    uid = get_user_attribute(user, "sub")

    try:
        ProjectUsers(name, uid).delete()
    except DoesNotExist:
        raise PortalError(409, "Unable to delete")

    return {"success": True}


@router.attach("/dportal/admin/projects/{name}/users", "post")
def add_user_to_project(event, context):
    name = event["pathParameters"]["name"]
    body_dict = json.loads(event.get("body"))
    emails = body_dict.get("emails")
    users = [get_user_from_attribute("email", email) for email in emails]

    print(users)
    print(name)
    try:
        Projects.get(name)
    except DoesNotExist:
        raise PortalError(404, "Project not found")

    with ProjectUsers.batch_write() as batch:
        for user in users:
            user_id = get_user_attribute(user, "sub")
            user_project = ProjectUsers(name, user_id)
            batch.save(user_project)

    return {"success": True}


#
# Project Functions
#


@router.attach("/dportal/admin/projects/{name}", "delete")
def delete_project(event, context):
    name = event["pathParameters"]["name"]

    try:
        project = Projects.get(name)
    except DoesNotExist:
        raise PortalError(404, "Project not found")

    keys = list_s3_prefix(DPORTAL_BUCKET, f"projects/{project.name}/")
    delete_s3_objects(DPORTAL_BUCKET, keys)

    with ProjectUsers.batch_write() as batch:
        for entry in ProjectUsers.scan():
            batch.delete(entry)

    project.delete()

    return {"success": True}


@router.attach("/dportal/admin/projects/{name}", "put")
def update_project(event, context):
    name = event.get("path").get("name")
    body_dict = json.loads(event.get("body"))
    description = body_dict.get("description")
    project = Projects.get(name)
    project.description = description
    project.save()

    return project.attribute_values


@router.attach("/dportal/admin/projects", "post")
def create_project(event, context):
    body_dict = json.loads(event.get("body"))
    name = body_dict.get("name")
    description = body_dict.get("description")
    vcf_path = body_dict.get("vcf")
    tbi_path = body_dict.get("tbi")
    json_path = body_dict.get("json")

    if Projects.count(name):
        raise PortalError(409, "Project already exists")

    # TODO tag s3 objects with project name
    # add a life cycle policy to delete objects unless tagged to avoid
    # zombie projects

    project = Projects(
        name,
        description=description,
        vcf=vcf_path,
        tbi=tbi_path,
        json=json_path,
    )
    project.save()

    return project.attribute_values


@router.attach("/dportal/admin/projects", "get")
def list_projects(event, context):
    projects = Projects.scan()
    return [project.attribute_values for project in projects]
