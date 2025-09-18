import os
import json
from time import time

from shared.apiutils import LambdaRouter, PortalError
from utils.models import (
    Projects,
    ProjectUsers,
    CliUpload,
)
from utils.s3_util import get_presigned_url, get_upload_presigned_url, list_s3_prefix

DPORTAL_BUCKET = os.environ.get("DPORTAL_BUCKET")
router = LambdaRouter()


@router.attach("/dportal/cli", "post")
def cli_handler(event, context):
    sub = event["requestContext"]["authorizer"]["claims"]["sub"]
    body = json.loads(event["body"])
    identity_id = event["requestContext"]["authorizer"]["claims"]["custom:identity_id"]

    try:
        mode = body.get("mode")

        match mode:
            case "projects":
                user_projects = ProjectUsers.uid_index.query(sub)
                projects = [
                    Projects.get(user_project.name).to_dict()
                    for user_project in user_projects
                ]
                return [
                    {"name": project["name"], "description": project["description"]}
                    for project in projects
                ]
            case "files":
                if project := body.get("project"):
                    ProjectUsers.get(project, sub)
                    project = Projects.get(project)
                    return [file for file in project.files]
                else:
                    return [
                        file.removeprefix(f"private/{identity_id}/")
                        for file in list_s3_prefix(
                            DPORTAL_BUCKET, f"private/{identity_id}/"
                        )
                    ]
            case "download":
                files = body.get("files", [])

                if project := body.get("project"):
                    ProjectUsers.get(project, sub)
                    project = Projects.get(project)
                    project_files = project.files

                    if not all(file in project_files for file in files):
                        raise PortalError(
                            404, "Some or all of these files do not exist."
                        )

                    urls = [
                        get_presigned_url(
                            DPORTAL_BUCKET,
                            f"projects/{project.name}/project-files/{file}",
                        )
                        for file in files
                    ]
                    return urls
                else:
                    user_files = [
                        file.removeprefix(f"private/{identity_id}/")
                        for file in list_s3_prefix(
                            DPORTAL_BUCKET, f"private/{identity_id}/"
                        )
                    ]
                    if not all(file in user_files for file in files):
                        raise PortalError(
                            404, "Some or all of these files do not exist."
                        )
                    urls = [
                        get_presigned_url(
                            DPORTAL_BUCKET,
                            f"private/{identity_id}/{file}",
                        )
                        for file in files
                    ]
                    return urls
            case "upload":
                files = body.get("files", [])
                sizes = [s / (1024 * 1024) for s in body.get("sizes", [])]
                epoch_now = int(time())

                if len(files) != len(sizes):
                    raise PortalError(400, "Invalid payload.")

                if project := body.get("project"):
                    ProjectUsers.get(project, sub)
                    project = Projects.get(project)
                    allowed_uploads = list(
                        CliUpload.project_name_index.query(
                            project.name, CliUpload.uid == sub
                        )
                    )

                    for f, s in zip(files, sizes):
                        if not any(
                            upload.file_name == f
                            and s <= upload.max_mb
                            and upload.expiration > epoch_now
                            for upload in allowed_uploads
                        ):
                            raise PortalError(
                                403,
                                "Upload not authorized. Please check filename and size.",
                            )

                    urls = [
                        get_upload_presigned_url(
                            DPORTAL_BUCKET,
                            f"staging/projects/{project.name}/project-files/{file}",
                            expiration=[
                                u for u in allowed_uploads if u.file_name == file
                            ][0].expiration,
                            max_bytes=[
                                u for u in allowed_uploads if u.file_name == file
                            ][0].max_mb
                            * 1024
                            * 1024,
                        )
                        for file in files
                    ]
                    return urls
                else:
                    raise PortalError(
                        403,
                        "This facility is not provided.",
                    )
    except PortalError as e:
        raise e
    except ProjectUsers.DoesNotExist:
        print("User does not have access to project")
        raise PortalError(403, "Access denied. You do not have access to this project.")
    except Exception as e:
        print(f"Error: {e}")
        raise PortalError(500, "Error please contact the administrator")
