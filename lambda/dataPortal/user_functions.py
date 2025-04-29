import os
import json

from shared.apiutils import LambdaRouter, PortalError
from utils.models import Projects, ProjectUsers, SavedQueries
from utils.s3_util import get_presigned_url
from utils.lambda_util import invoke_lambda_function

router = LambdaRouter()
DPORTAL_BUCKET = os.environ.get("DPORTAL_BUCKET")
COHORT_MAKER_LAMBDA = os.environ.get("COHORT_MAKER_LAMBDA")


@router.attach("/dportal/projects", "get")
def list_all_projects(event, context):
    sub = event["requestContext"]["authorizer"]["claims"]["sub"]
    query_params = event.get("queryStringParameters", {})

    # Check if pagination parameters are provided
    # This validation is necessary to get list for dropdown without pagination
    # and to get list with pagination
    if query_params:
        # Pagination, fetch projects with limit and last_evaluated_key
        params = {"limit": 10}
        limit = query_params.get("limit", None)
        last_evaluated_key = query_params.get("last_evaluated_key", None)

        if limit:
            params["limit"] = int(limit)
        if last_evaluated_key:
            params["last_evaluated_key"] = json.loads(last_evaluated_key)

        user_projects = ProjectUsers.uid_index.query(sub, **params)
    else:
        # No pagination, fetch all projects
        user_projects = ProjectUsers.uid_index.query(sub)

    projects = [
        Projects.get(user_project.name).to_dict() for user_project in user_projects
    ]

    last_evaluated_key = (
        json.dumps(user_projects.last_evaluated_key)
        if user_projects.last_evaluated_key
        else user_projects.last_evaluated_key
    )

    return {"success": True, "data": projects, "last_evaluated_key": last_evaluated_key}


@router.attach("/dportal/my-projects", "get")
def list_my_projects(event, context):
    query_params = event.get("queryStringParameters", {})
    sub = event["requestContext"]["authorizer"]["claims"]["sub"]

    params = {"limit": 10}
    if query_params:
        limit = query_params.get("limit", None)
        last_evaluated_key = query_params.get("last_evaluated_key", None)
        if limit:
            params["limit"] = int(limit)
        if last_evaluated_key:
            params["last_evaluated_key"] = json.loads(last_evaluated_key)

    user_projects = ProjectUsers.uid_index.query(sub, **params)
    data = [Projects.get(user_project.name).to_dict() for user_project in user_projects]
    last_evaluated_key = (
        json.dumps(user_projects.last_evaluated_key)
        if user_projects.last_evaluated_key
        else user_projects.last_evaluated_key
    )
    return {"success": True, "data": data, "last_evaluated_key": last_evaluated_key}


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

    return get_presigned_url(DPORTAL_BUCKET, f"projects/{name}/project-files/{prefix}")


@router.attach("/dportal/queries", "get")
def get_saved_queries(event, context):
    sub = event["requestContext"]["authorizer"]["claims"]["sub"]
    entries = [
        {
            "name": entry.name,
            "description": entry.description,
            "query": json.loads(entry.savedQuery),
        }
        for entry in SavedQueries.query(sub)
    ]

    return entries


@router.attach("/dportal/queries", "post")
def save_query(event, context):
    sub = event["requestContext"]["authorizer"]["claims"]["sub"]
    body_dict = json.loads(event.get("body"))
    name = body_dict.get("name")
    description = body_dict.get("description")
    query = body_dict.get("query")
    entry = SavedQueries(
        sub, name, description=description, savedQuery=json.dumps(query)
    )
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


@router.attach("/dportal/cohort", "post")
def create_cohort(event, context):
    body_dict = json.loads(event.get("body"))
    sub = event["requestContext"]["authorizer"]["claims"]["sub"]
    body_dict["sub"] = sub

    invoke_lambda_function(COHORT_MAKER_LAMBDA, body_dict, True)

    return {"success": True}
