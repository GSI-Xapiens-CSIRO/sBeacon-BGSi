import os
import json

from shared.apiutils import LambdaRouter, PortalError
from utils.models import (
    Projects,
    ProjectUsers,
)
from utils.s3_util import get_presigned_url, get_upload_presigned_url

DPORTAL_BUCKET = os.environ.get("DPORTAL_BUCKET")
router = LambdaRouter()


@router.attach("/dportal/cli", "post")
def cli_handler(event, context):
    sub = event["requestContext"]["authorizer"]["claims"]["sub"]
    body = json.loads(event["body"])

    try:
        mode = body.get("mode")

        match mode:
            case "list_projects":
                user_projects = ProjectUsers.uid_index.query(sub)
                projects = [
                    Projects.get(user_project.name).to_dict()
                    for user_project in user_projects
                ]
                return [
                    {"name": project["name"], "description": project["description"]}
                    for project in projects
                ]
            case "list_files":
                project = body.get("project")
                ProjectUsers.get(project, sub)
                project = Projects.get(project)
                return [file for file in project.files]
            case "download":
                project = body.get("project")
                files = body.get("files", [])
                ProjectUsers.get(project, sub)
                project = Projects.get(project)
                urls = [
                    get_presigned_url(
                        DPORTAL_BUCKET, f"projects/{project.name}/project-files/{file}"
                    )
                    for file in files
                ]
                return urls
            case "upload":
                project = body.get("project")
                identity_id = event["requestContext"]["authorizer"]["claims"]["custom:identity_id"]
                files = body.get("files", [])
                ProjectUsers.get(project, sub)
                project = Projects.get(project)
                urls = [
                    get_upload_presigned_url(
                        DPORTAL_BUCKET, f"private/{identity_id}/uploads/{project.name}/{file}"
                    )
                    for file in files
                ]
                return urls
    except ProjectUsers.DoesNotExist:
        print("User does not have access to project")
        raise PortalError(403, "Access denied. You do not have access to this project.")
    except Exception as e:
        print(f"Error: {e}")
        raise PortalError(500, "Error please contact the administrator")
