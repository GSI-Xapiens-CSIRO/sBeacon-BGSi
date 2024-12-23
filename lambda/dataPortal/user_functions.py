import os
import json

from shared.apiutils import LambdaRouter, PortalError
from utils.models import Projects, ProjectUsers, SavedQueries
from utils.s3_util import get_presigned_url

router = LambdaRouter()
DPORTAL_BUCKET = os.environ.get("DPORTAL_BUCKET")


@router.attach("/dportal/projects", "get")
def list_my_projects(event, context):
    sub = event["requestContext"]["authorizer"]["claims"]["sub"]
    user_projects = ProjectUsers.uid_index.query(sub)

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
    except ProjectUsers.DoesNotExist:
        raise PortalError(404, "User not found in project")
    except Projects.DoesNotExist:
        raise PortalError(404, "Project not found")

    if prefix not in project.files:
        raise PortalError(404, "File not found in project")

    return get_presigned_url(DPORTAL_BUCKET, f"projects/{name}/{prefix}")


@router.attach("/dportal/queries", "get")
def get_saved_queries(event, context):
    entries = [entry.attribute_values for entry in SavedQueries.scan()]

    def to_json(entry):
        entry["query"] = json.loads(entry["query"])
        return entry

    return list(map(to_json, entries))


@router.attach("/dportal/queries", "post")
def save_query(event, context):
    sub = event["requestContext"]["authorizer"]["claims"]["sub"]
    body_dict = json.loads(event.get("body"))
    name = body_dict.get("name")
    description = body_dict.get("description")
    query = body_dict.get("query")
    entry = SavedQueries(sub, name, description=description, query=json.dumps(query))
    entry.save()

    return {"success": True}


@router.attach("/dportal/queries/{name}", "delete")
def delete_query(event, context):
    sub = event["requestContext"]["authorizer"]["claims"]["sub"]
    name = event["pathParameters"]["name"]

    try:
        entry = SavedQueries.get(sub, name)
        entry.delete()
    except SavedQueries.DoesNotExist:
        raise PortalError(404, "Query not found")

    return {"success": True}
