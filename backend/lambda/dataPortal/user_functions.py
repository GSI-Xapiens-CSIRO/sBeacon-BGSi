import os

from utils.router import LambdaRouter, PortalError
from utils.models import Projects, ProjectUsers
from utils.s3_util import get_presigned_url

from pynamodb.exceptions import DoesNotExist

router = LambdaRouter()
DPORTAL_BUCKET = os.environ.get("DPORTAL_BUCKET")


@router.attach("/dportal/projects", "get")
def list_my_projects(event, context):
    sub = event["requestContext"]["authorizer"]["claims"]["sub"]
    user_projects = list(ProjectUsers.scan(ProjectUsers.uid == sub))

    projects = [
        Projects.get(user_project.name).to_dict() for user_project in user_projects
    ]

    return projects


@router.attach("/dportal/projects/{name}/file", "get")
def get_file_presigned_url(event, context):
    sub = event["requestContext"]["authorizer"]["claims"]["sub"]
    name = event["pathParameters"]["name"]
    prefix = event["queryStringParameters"].get("prefix")

    if not prefix:
        raise PortalError(400, "Missing file parameter")
    try:
        # ensure user has access to project
        ProjectUsers.get(name, sub)
        # get project
        project = Projects.get(name)
    except DoesNotExist:
        raise PortalError(404, "Project not found")

    if prefix not in project.files:
        raise PortalError(404, "File not found in project")

    return get_presigned_url(DPORTAL_BUCKET, prefix)
