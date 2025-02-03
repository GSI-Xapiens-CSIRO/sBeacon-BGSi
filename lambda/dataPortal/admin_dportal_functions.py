import json
import os
import re

from utils.models import Projects, ProjectUsers
from pynamodb.exceptions import DoesNotExist
from utils.s3_util import list_s3_prefix, list_s3_folder, delete_s3_objects
from utils.cognito import get_user_from_attribute, get_user_attribute, list_users
from utils.lambda_util import invoke_lambda_function
from shared.cognitoutils import authenticate_manager
from shared.apiutils import LambdaRouter, PortalError


router = LambdaRouter()
DPORTAL_BUCKET = os.environ.get("DPORTAL_BUCKET")
ATHENA_METADATA_BUCKET = os.environ.get("ATHENA_METADATA_BUCKET")
SUBMIT_LAMBDA = os.environ.get("SUBMIT_LAMBDA")
INDEXER_LAMBDA = os.environ.get("INDEXER_LAMBDA")


#
# Files' Admin Functions
#
@router.attach("/dportal/admin/folders", "get", authenticate_manager)
def list_folders(event, context):
    folders = list_s3_folder(DPORTAL_BUCKET, "private/")
    identity_ids = [file.strip("/").split("/")[-1] for file in folders]
    all_users = list_users()
    users_with_identity = {
        user["custom:identity_id"]: user
        for user in all_users
        if user.get("custom:identity_id")
    }
    active_users = [
        users_with_identity[identity_id]
        for identity_id in identity_ids
        if identity_id in users_with_identity
    ]
    inactive_user_folders = [
        identity_id
        for identity_id in identity_ids
        if identity_id not in users_with_identity
    ]
    return {
        "active": active_users,
        "inactive": inactive_user_folders,
    }


@router.attach("/dportal/admin/folders/{folder}", "delete", authenticate_manager)
def delete_folder(event, context):
    folder = event["pathParameters"]["folder"]
    keys = list_s3_prefix(DPORTAL_BUCKET, f"private/{folder}/")
    delete_s3_objects(DPORTAL_BUCKET, keys)

    return {"success": True}


#
# Project Admin Functions
#


@router.attach("/dportal/admin/projects/{name}/users", "get", authenticate_manager)
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


@router.attach(
    "/dportal/admin/projects/{name}/users/{email}", "delete", authenticate_manager
)
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


@router.attach("/dportal/admin/projects/{name}/users", "post", authenticate_manager)
def add_user_to_project(event, context):
    name = event["pathParameters"]["name"]
    body_dict = json.loads(event.get("body"))
    emails = body_dict.get("emails")
    users = []

    for email in emails:
        try:
            user = get_user_from_attribute("email", email)
            users.append(user)
        except PortalError as e:
            return {"success": False, "message": e.error_message}

    try:
        Projects.get(name)
    except DoesNotExist:
        return {"success": False, "message": "Project not found"}

    with ProjectUsers.batch_write() as batch:
        for user in users:
            user_id = get_user_attribute(user, "sub")
            user_project = ProjectUsers(name, user_id)
            batch.save(user_project)

    return {"success": True, "message": ""}


#
# Project Functions
#


@router.attach("/dportal/admin/projects/{name}", "delete", authenticate_manager)
def delete_project(event, context):
    name = event["pathParameters"]["name"]

    try:
        project = Projects.get(name)
    except DoesNotExist:
        raise PortalError(404, "Project not found")

    keys = list_s3_prefix(DPORTAL_BUCKET, f"projects/{project.name}/")
    delete_s3_objects(DPORTAL_BUCKET, keys)

    for dataset_id in project.ingested_datasets:
        cache_prefixes = [
            # entities
            f"individuals-cache/{name}:{dataset_id}",
            f"biosamples-cache/{name}:{dataset_id}",
            f"runs-cache/{name}:{dataset_id}",
            f"analyses-cache/{name}:{dataset_id}",
            f"datasets-cache/{name}:{dataset_id}",
            # terms
            f"terms-cache/individuals-{name}:{dataset_id}",
            f"terms-cache/biosamples-{name}:{dataset_id}",
            f"terms-cache/runs-{name}:{dataset_id}",
            f"terms-cache/analyses-{name}:{dataset_id}",
            f"terms-cache/datasets-{name}:{dataset_id}",
        ]
        print(cache_prefixes)
        delete_s3_objects(ATHENA_METADATA_BUCKET, cache_prefixes)

    with ProjectUsers.batch_write() as batch:
        for entry in ProjectUsers.scan():
            batch.delete(entry)

    project.delete()

    return {"success": True}


@router.attach("/dportal/admin/projects/{name}", "put", authenticate_manager)
def update_project(event, context):
    name = event["pathParameters"]["name"]
    body_dict = json.loads(event.get("body"))
    description = body_dict.get("description")
    project = Projects.get(name)
    # file diff
    current_files = set(body_dict.get("files") or [])
    initial_files = project.files or set()
    deleted_files = initial_files - current_files
    # update entry
    project.description = description
    project.save()
    # delete file diff
    delete_s3_objects(
        DPORTAL_BUCKET,
        [f"projects/{name}/{file}" for file in deleted_files],
    )

    return project.to_dict()


@router.attach("/dportal/admin/projects", "post", authenticate_manager)
def create_project(event, context):
    body_dict = json.loads(event.get("body"))
    name = body_dict.get("name").strip()

    if not len(name):
        raise PortalError(400, "Project name cannot be empty")

    # sanitise name
    name = re.sub(r"[,.:;/\\]", "-", name)
    description = body_dict.get("description")

    if Projects.count(name):
        raise PortalError(409, "Project already exists")

    # TODO tag s3 objects with project name
    # add a life cycle policy to delete objects unless tagged to avoid
    # zombie projects

    project = Projects(
        name,
        description=description,
    )
    project.save()
    return project.to_dict()


@router.attach("/dportal/admin/projects", "get", authenticate_manager)
def list_projects(event, context):
    query_params = event.get("queryStringParameters", {})
    params = {"limit": 10}
    if query_params:
        limit = query_params.get("limit", None)
        last_evaluated_key = query_params.get("last_evaluated_key", None)
        if limit:
            params["limit"] = int(limit)
        if last_evaluated_key:
            params["last_evaluated_key"] = json.loads(last_evaluated_key)

    projects = Projects.scan(**params)
    data = [project.to_dict() for project in projects]
    last_evaluated_key = (
        json.dumps(projects.last_evaluated_key)
        if projects.last_evaluated_key
        else projects.last_evaluated_key
    )
    return {"success": True, "data": data, "last_evaluated_key": last_evaluated_key}


#
# sBeacon Functions
#


@router.attach(
    "/dportal/admin/projects/{name}/ingest/{dataset}", "post", authenticate_manager
)
def ingest_dataset_to_sbeacon(event, context):
    body_dict = json.loads(event.get("body"))
    project_name = event["pathParameters"]["name"]
    dataset_id = event["pathParameters"]["dataset"].strip()

    if not len(dataset_id):
        raise PortalError(400, "Dataset id cannot be empty")

    # sanitise dataset_id
    dataset_id = re.sub(r"[,.:;/\\]", "-", dataset_id)

    payload = {
        "s3Payload": body_dict["s3Payload"],
        "vcfLocations": body_dict["vcfLocations"],
        "projectName": project_name,
        "datasetId": dataset_id,
    }
    project = Projects.get(project_name)
    response = invoke_lambda_function(SUBMIT_LAMBDA, payload)

    if "success" in response and response["success"]:
        project.update(actions=[Projects.ingested_datasets.add([dataset_id])])

    return response


@router.attach(
    "/dportal/admin/projects/{name}/ingest/{dataset}", "delete", authenticate_manager
)
def un_ingest_dataset_from_sbeacon(event, context):
    project_name = event["pathParameters"]["name"]
    dataset_id = event["pathParameters"]["dataset"]

    cache_prefixes = [
        # entities
        f"individuals-cache/{project_name}:{dataset_id}",
        f"biosamples-cache/{project_name}:{dataset_id}",
        f"runs-cache/{project_name}:{dataset_id}",
        f"analyses-cache/{project_name}:{dataset_id}",
        f"datasets-cache/{project_name}:{dataset_id}",
        # terms
        f"terms-cache/individuals-{project_name}:{dataset_id}",
        f"terms-cache/biosamples-{project_name}:{dataset_id}",
        f"terms-cache/runs-{project_name}:{dataset_id}",
        f"terms-cache/analyses-{project_name}:{dataset_id}",
        f"terms-cache/datasets-{project_name}:{dataset_id}",
    ]
    delete_s3_objects(ATHENA_METADATA_BUCKET, cache_prefixes)

    project = Projects.get(project_name)
    project.update(actions=[Projects.ingested_datasets.delete([dataset_id])])

    return {
        "success": True,
        "message": "Dataset removed from sBeacon. Please index when you have un-ingested all the desired datasets.",
    }


@router.attach("/dportal/admin/sbeacon/index", "post", authenticate_manager)
def index_sbeacon(event, context):
    payload = {
        "reIndexTables": True,
        "reIndexOntologyTerms": True,
    }
    invoke_lambda_function(INDEXER_LAMBDA, payload, event=True)

    return {"success": True, "message": "Indexing started asynchonously"}
