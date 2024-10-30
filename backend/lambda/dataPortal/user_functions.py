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
    user_projects = ProjectUsers.scan(ProjectUsers.uid == sub)

    return [user_project.attribute_values for user_project in user_projects]


@router.attach("/dportal/projects/{name}/file", "get")
def get_file_presigned_url(event, context):
    sub = event["requestContext"]["authorizer"]["claims"]["sub"]
    name = event["pathParameters"]["name"]
    file = event["queryStringParameters"].get("file")

    if not file:
        raise PortalError(400, "Missing file parameter")
    try:
        # ensure user has access to project
        ProjectUsers.get(name, sub)
        # get project
        project = Projects.get(name)
    except DoesNotExist:
        raise PortalError(404, "Project not found")

    try:
        prefix = project.attribute_values[file]
    except KeyError:
        raise PortalError(404, "File not found in project")

    return get_presigned_url(DPORTAL_BUCKET, prefix)
