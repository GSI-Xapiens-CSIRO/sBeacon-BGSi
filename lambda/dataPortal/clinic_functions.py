import os
import json

from shared.apiutils import LambdaRouter, PortalError
from utils.models import (
    Projects,
    ProjectUsers,
    ClinicJobs,
    ClinicalAnnotations,
    ClinicalVariants,
)
from utils.cognito import get_user_from_attribute, get_user_attribute

router = LambdaRouter()
DPORTAL_BUCKET = os.environ.get("DPORTAL_BUCKET")


@router.attach("/dportal/projects/{project}/clinical-workflows", "get")
def list_jobs(event, context):
    print(f"Event received: {json.dumps(event)}")
    sub = event["requestContext"]["authorizer"]["claims"]["sub"]
    project = event["pathParameters"]["project"]
    params = event["queryStringParameters"] or dict()
    limit = params.get("limit", "10") or "10"
    last_evaluated_key = params.get("last_evaluated_key", "null") or "null"

    try:
        # ensure user has access to project
        ProjectUsers.get(project, sub)
        # get project
        Projects.get(project)
        # get jobs
        jobs = ClinicJobs.project_index.query(
            project,
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
        "success": True,
        "jobs": [
            {
                "job_id": job.job_id,
                "input_vcf": job.input_vcf,
                "job_status": job.job_status,
                "failed_step": job.failed_step,
                "error_message": job.error_message,
            }
            for job in jobs
        ],
        "last_evaluated_key": (
            json.dumps(jobs.last_evaluated_key) if jobs.last_evaluated_key else None
        ),
    }


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
        annotation_name = event["requestContext"]["requestId"]
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
        uid=sub,
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

    response = {
        "annotations": [],
    }

    for annot in annotations:
        entry = {
            "name": annot.annotation_name,
            "annotation": annot.annotation,
            "createdAt": annot.created_at,
            "variants": json.loads(annot.variants),
        }
        try:
            user = get_user_from_attribute("sub", annot.uid)
            entry["user"] = {
                "firstName": get_user_attribute(user, "given_name"),
                "lastName": get_user_attribute(user, "family_name"),
                "email": get_user_attribute(user, "email"),
            }
        except PortalError:
            user = None
        finally:
            response["annotations"].append(entry)

    response["last_evaluated_key"] = (
        json.dumps(annotations.last_evaluated_key)
        if annotations.last_evaluated_key
        else None
    )

    return response


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


@router.attach(
    "/dportal/projects/{project}/clinical-workflows/{job_id}/variants", "post"
)
def save_variants(event, context):
    sub = event["requestContext"]["authorizer"]["claims"]["sub"]
    project = event["pathParameters"]["project"]
    job_id = event["pathParameters"]["job_id"]
    body = json.loads(event["body"])

    try:
        # ensure user has access to project
        ProjectUsers.get(project, sub)
        # get project
        Projects.get(project)
        # get collection name, comment and variants
        collection_name = event["requestContext"]["requestId"]
        comment = body["comment"]
        variants = body["variants"]
        variants_annotations = [None for _ in variants]
        annotations = ClinicalAnnotations.query(f"{project}:{job_id}")

        for annot in annotations:
            annotated_variants = json.loads(annot.variants)
            for idx, var in enumerate(variants):
                if var in annotated_variants:
                    variants_annotations[idx] = annot.annotation
    except ProjectUsers.DoesNotExist:
        raise PortalError(404, "User not found in project")
    except Projects.DoesNotExist:
        raise PortalError(404, "Project not found")
    except KeyError:
        raise PortalError(400, "Missing required field")

    annot = ClinicalVariants(
        f"{project}:{job_id}",
        collection_name,
        comment=comment,
        variants=json.dumps(variants),
        variants_annotations=json.dumps(variants_annotations),
        uid=sub,
    )
    annot.save()

    return {"success": True, "message": "Variants collection saved"}


@router.attach(
    "/dportal/projects/{project}/clinical-workflows/{job_id}/variants", "get"
)
def get_variants(event, context):
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
        # get variants
        variants = ClinicalVariants.query(
            f"{project}:{job_id}",
            limit=int(limit),
            last_evaluated_key=json.loads(last_evaluated_key),
        )
    except ProjectUsers.DoesNotExist:
        raise PortalError(404, "User not found in project")
    except Projects.DoesNotExist:
        raise PortalError(404, "Project not found")
    except ClinicalVariants.DoesNotExist:
        raise PortalError(404, "Variants collection not found")

    response = {
        "variants": [],
    }

    for var in variants:
        entry = {
            "name": var.collection_name,
            "comment": var.comment,
            "createdAt": var.created_at,
            "variants": json.loads(var.variants),
            "annotations": json.loads(var.variants_annotations),
        }
        try:
            user = get_user_from_attribute("sub", var.uid)
            entry["user"] = {
                "firstName": get_user_attribute(user, "given_name"),
                "lastName": get_user_attribute(user, "family_name"),
                "email": get_user_attribute(user, "email"),
            }
        except PortalError:
            user = None
        finally:
            response["variants"].append(entry)

    response["last_evaluated_key"] = (
        json.dumps(variants.last_evaluated_key) if variants.last_evaluated_key else None
    )

    return response


@router.attach(
    "/dportal/projects/{project}/clinical-workflows/{job_id}/variants/{name}",
    "delete",
)
def delete_variants(event, context):
    sub = event["requestContext"]["authorizer"]["claims"]["sub"]
    project = event["pathParameters"]["project"]
    job_id = event["pathParameters"]["job_id"]
    name = event["pathParameters"]["name"]

    try:
        # ensure user has access to project
        ProjectUsers.get(project, sub)
        # get project
        Projects.get(project)
        annot = ClinicalVariants(f"{project}:{job_id}", name)
        annot.delete()
    except ProjectUsers.DoesNotExist:
        raise PortalError(404, "User not found in project")
    except Projects.DoesNotExist:
        raise PortalError(404, "Project not found")
    except ClinicalVariants.DoesNotExist:
        raise PortalError(404, "Variants collection not found")
    except KeyError:
        raise PortalError(400, "Missing required field")

    return {"success": True, "message": "Variants collection deleted"}
