import os
import json

from shared.apiutils import LambdaRouter, PortalError
from utils.models import Projects, ProjectUsers, ClinicalAnnotations
from utils.s3_util import get_presigned_url

router = LambdaRouter()
DPORTAL_BUCKET = os.environ.get("DPORTAL_BUCKET")


@router.attach(
    "/dportal/projects/{project}/clinical-workflows/{job_id}/annotations", "post"
)
def save_annotations(event, context):
    sub = event["requestContext"]["authorizer"]["claims"]["sub"]
    project = event["pathParameters"]["project"]
    job_id = event["pathParameters"]["job_id"]
    body = json.loads(event["body"])

    try:
        # ensure user has access to project
        ProjectUsers.get(project, sub)
        # get project
        Projects.get(project)
        # get annotation name, annotation and variants
        annotation_name = body["name"]
        annotation = body["annotation"]
        variants = body["variants"]
    except ProjectUsers.DoesNotExist:
        raise PortalError(404, "User not found in project")
    except Projects.DoesNotExist:
        raise PortalError(404, "Project not found")
    except KeyError:
        raise PortalError(400, "Missing required field")

    annot = ClinicalAnnotations(
        f"{project}:{job_id}",
        annotation_name,
        annotation=annotation,
        variants=json.dumps(variants),
    )
    annot.save()

    return {"success": True, "message": "Annotation saved"}


@router.attach(
    "/dportal/projects/{project}/clinical-workflows/{job_id}/annotations", "get"
)
def get_annotations(event, context):
    sub = event["requestContext"]["authorizer"]["claims"]["sub"]
    project = event["pathParameters"]["project"]
    job_id = event["pathParameters"]["job_id"]
    params = event["queryStringParameters"] or dict()
    limit = params.get("limit", "10") or "10"
    last_evaluated_key = params.get("last_evaluated_key", "null") or "null"

    try:
        # ensure user has access to project
        ProjectUsers.get(project, sub)
        # get project
        Projects.get(project)
        # get annotations
        annotations = ClinicalAnnotations.query(
            f"{project}:{job_id}",
            limit=int(limit),
            last_evaluated_key=json.loads(last_evaluated_key),
        )
    except ProjectUsers.DoesNotExist:
        raise PortalError(404, "User not found in project")
    except Projects.DoesNotExist:
        raise PortalError(404, "Project not found")
    except ClinicalAnnotations.DoesNotExist:
        raise PortalError(404, "Annotations not found")

    return {
        "annotations": [
            {
                "name": annot.annotation_name,
                "annotation": annot.annotation,
                "variants": json.loads(annot.variants),
            }
            for annot in annotations
        ],
        "last_evaluated_key": (
            json.dumps(annotations.last_evaluated_key)
            if annotations.last_evaluated_key
            else None
        ),
    }


@router.attach(
    "/dportal/projects/{project}/clinical-workflows/{job_id}/annotations/{name}",
    "delete",
)
def delete_annotations(event, context):
    sub = event["requestContext"]["authorizer"]["claims"]["sub"]
    project = event["pathParameters"]["project"]
    job_id = event["pathParameters"]["job_id"]
    name = event["pathParameters"]["name"]

    try:
        # ensure user has access to project
        ProjectUsers.get(project, sub)
        # get project
        Projects.get(project)
        annot = ClinicalAnnotations(f"{project}:{job_id}", name)
        annot.delete()
    except ProjectUsers.DoesNotExist:
        raise PortalError(404, "User not found in project")
    except Projects.DoesNotExist:
        raise PortalError(404, "Project not found")
    except ClinicalAnnotations.DoesNotExist:
        raise PortalError(404, "Annotation not found")
    except KeyError:
        raise PortalError(400, "Missing required field")

    return {"success": True, "message": "Annotation deleted"}
