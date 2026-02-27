import json
import os
import re
from time import time

from utils.models import Projects, ProjectUsers
from pynamodb.exceptions import DoesNotExist
from utils.s3_util import list_s3_prefix, list_s3_folder, delete_s3_objects
from utils.cognito import get_user_from_attribute, get_user_attribute, list_users
from utils.lambda_util import invoke_lambda_function
from shared.cognitoutils import authenticate_manager, require_permissions
from shared.apiutils import LambdaRouter, PortalError
from shared.dynamodb.locks import acquire_lock
from utils.models import (
    Projects,
    ProjectUsers,
    CliUpload,
)

router = LambdaRouter()
DPORTAL_BUCKET = os.environ.get("DPORTAL_BUCKET")
ATHENA_METADATA_BUCKET = os.environ.get("ATHENA_METADATA_BUCKET")
SUBMIT_LAMBDA = os.environ.get("SUBMIT_LAMBDA")
INDEXER_LAMBDA = os.environ.get("INDEXER_LAMBDA")


#
# Files' Admin Functions
#
@router.attach("/dportal/admin/folders", "get", require_permissions('file_management.read'))
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


@router.attach("/dportal/admin/folders/{folder}", "delete", require_permissions('file_management.delete'))
def delete_folder(event, context):
    folder = event["pathParameters"]["folder"]
    keys = list_s3_prefix(DPORTAL_BUCKET, f"private/{folder}/")
    delete_s3_objects(DPORTAL_BUCKET, keys)

    return {"success": True}


#
# Project Admin Functions
#


@router.attach("/dportal/admin/projects/{name}/users", "get", require_permissions('project_management.read'))
def list_project_users(event, context):
    name = event["pathParameters"]["name"]

    try:
        Projects.get(name)
    except DoesNotExist:
        raise PortalError(404, "Project not found")

    user_projects = ProjectUsers.query(name)
    users = []
    
    for user_project in user_projects:
        try:
            user = get_user_from_attribute("sub", user_project.uid)
            users.append({
                "firstName": get_user_attribute(user, "given_name"),
                "lastName": get_user_attribute(user, "family_name"),
                "email": get_user_attribute(user, "email"),
            })
        except (PortalError, Exception) as e:
            print(f"User {user_project.uid} not found in Cognito, skipping... Error: {str(e)}")
            continue

    return users


@router.attach(
    "/dportal/admin/projects/{name}/users/{email}", "delete", require_permissions('project_management.delete')
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


@router.attach("/dportal/admin/projects/{name}/users", "post", require_permissions('project_management.update'))
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


@router.attach(
    "/dportal/admin/projects/{name}/users/{email}/upload", "post", require_permissions('project_management.create')
)
def admin_user_cli_add_upload(event, context):
    name = event["pathParameters"]["name"]
    email = event["pathParameters"]["email"]
    body_dict = json.loads(event.get("body"))

    try:
        user = get_user_from_attribute("email", email)
        sub = get_user_attribute(user, "sub")
        request_id = event["requestContext"]["requestId"]
        max_mb = body_dict["maxMB"]
        file_name = body_dict["fileName"]
        expiration = body_dict["expirationMins"]
        ProjectUsers.get(name, sub)
    except DoesNotExist:
        return {"success": False, "message": "User not found in project"}
    except KeyError as e:
        return {"success": False, "message": f"Missing parameter: {e}"}
    except PortalError as e:
        return {"success": False, "message": e.error_message}

    upload = CliUpload(sub, request_id)
    upload.project_name = name
    upload.max_mb = max_mb
    upload.file_name = file_name
    upload.expiration = int(time()) + expiration * 60
    upload.save()

    return {"success": True}


@router.attach(
    "/dportal/admin/projects/{name}/users/{email}/upload/{upload_id}",
    "delete",
    require_permissions('project_management.delete'),
)
def admin_user_cli_remove_upload(event, context):
    email = event["pathParameters"]["email"]
    upload_id = event["pathParameters"]["upload_id"]

    try:
        user = get_user_from_attribute("email", email)
        sub = get_user_attribute(user, "sub")
        upload = CliUpload(sub, upload_id)
        upload.delete()
    except PortalError as e:
        return {"success": False, "message": e.error_message}
    except DoesNotExist:
        return {"success": False, "message": "Upload not found"}

    return {"success": True, "message": ""}


#
# Project Cli Functions
#


@router.attach("/dportal/admin/projects/{name}/upload", "get", require_permissions('project_management.read'))
def admin_get_project_uploads(event, context):
    name = event["pathParameters"]["name"]

    try:
        uploads = CliUpload.project_name_index.query(name)
        uploads = [
            upload.attribute_values
            for upload in uploads
            if upload.expiration > int(time())
        ]

        for upload in uploads:
            user = get_user_from_attribute("sub", upload["uid"])
            email = get_user_attribute(user, "email")
            upload["email"] = email
    except DoesNotExist:
        return {"success": False, "message": "Project not found"}

    return {"success": True, "uploads": uploads}


#
# Project Functions
#


@router.attach("/dportal/admin/projects/{name}", "delete", require_permissions('project_management.delete'))
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
        for entry in ProjectUsers.query(hash_key=name):
            batch.delete(entry)

    project.delete()

    payload = {
        "reIndexTables": True,
        "reIndexOntologyTerms": True,
    }
    invoke_lambda_function(INDEXER_LAMBDA, payload, event=True)

    return {"success": True}


@router.attach("/dportal/admin/projects/{name}", "put", require_permissions('project_management.update'))
def update_project(event, context):
    name = event["pathParameters"]["name"]
    body_dict = json.loads(event.get("body"))
    description = body_dict.get("description")
    project = Projects.get(name)
    # file diff
    current_files = set(body_dict.get("files") or [])
    initial_files = project.files or set()
    deleted_files = initial_files - current_files
    actions = [
        # update description
        Projects.description.set(description),
    ]
    if deleted_files:
        # remove from pending list if this files were in pending status
        Projects.pending_files.delete(deleted_files),
    # update entry
    project.update(actions=actions)
    if len(deleted_files) > 0:
        print(
            f'Deleting {",".join(deleted_files)} from project "{name}" by user "{event["requestContext"]["authorizer"]["claims"]["email"]}"'
        )
    # delete file diff
    delete_s3_objects(
        DPORTAL_BUCKET,
        [
            path
            for file in deleted_files
            for path in [
                f"projects/{name}/project-files/{file}",
                f"staging/projects/{name}/project-files/{file}",
            ]
        ],
    )

    return project.to_dict()


@router.attach("/dportal/admin/projects/{name}/errors", "delete", require_permissions('project_management.delete'))
def delete_project_errors(event, context):
    name = event["pathParameters"]["name"]

    project = Projects.get(name)
    project.error_messages = []
    project.save()

    return {"success": True}


@router.attach("/dportal/admin/projects", "post", require_permissions('project_management.create'))
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


@router.attach("/dportal/admin/projects", "get", require_permissions('project_management.read'))
def list_projects(event, context):
    sub = event["requestContext"]["authorizer"]["claims"]["sub"]
    query_params = event.get("queryStringParameters", {})
    params = {"limit": 10}
    search_term = None

    if query_params:
        limit = query_params.get("limit", None)
        last_evaluated_key = query_params.get("last_evaluated_key", None)
        search_term = query_params.get("search", None)
        if limit:
            params["limit"] = int(limit)
        if last_evaluated_key:
            params["last_evaluated_key"] = json.loads(last_evaluated_key)

    if search_term:
        search_term = search_term.lower()
        projects = Projects.scan(
            filter_condition=(
                Projects.name_lower.contains(search_term)
                | Projects.description_lower.contains(search_term)
            ),
            **params,
        )
    else:
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
    "/dportal/admin/projects/{name}/ingest/{dataset}", "post", require_permissions('project_management.create')
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
    "/dportal/admin/projects/{name}/ingest/{dataset}", "delete", require_permissions('project_management.delete')
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


@router.attach("/dportal/admin/sbeacon/index", "post", require_permissions('project_management.create'))
def index_sbeacon(event, context):
    request_id = event["requestContext"]["requestId"]
    payload = {
        "reIndexTables": True,
        "reIndexOntologyTerms": True,
        "ownerId": request_id,
    }

    try:
        lock = acquire_lock(
            lock_id="sbeacon-indexer",
            owner_id=request_id,
            ttl_seconds=600,
        )
        if not lock:
            return {
                "success": False,
                "message": "Unable to acquire lock. Another indexing process is already running.",
            }
        else:
            invoke_lambda_function(INDEXER_LAMBDA, payload, event=True)
            return {"success": True, "message": "Indexing started asynchonously"}
    except Exception as e:
        print(f"Error acquiring lock: {e}")
        return {
            "success": False,
            "message": "Unable to initiate indexing, please try again.",
        }
