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
from utils.lambda_util import invoke_lambda_function

router = LambdaRouter()
DPORTAL_BUCKET = os.environ.get("DPORTAL_BUCKET")
REPORTS_LAMBDA = os.environ.get("REPORTS_LAMBDA")
HUB_NAME = os.environ.get("HUB_NAME")


@router.attach("/dportal/projects/{project}/clinical-workflows", "get")
def list_jobs(event, context):
    print(f"Event received: {json.dumps(event)}")
    sub = event["requestContext"]["authorizer"]["claims"]["sub"]
    project = event["pathParameters"]["project"]
    params = event["queryStringParameters"] or dict()
    limit = params.get("limit", "10") or "10"
    last_evaluated_key = params.get("last_evaluated_key", "null") or "null"
    search_term = params.get("search", None)
    job_status = params.get("job_status", None)

    try:
        # ensure user has access to project
        ProjectUsers.get(project, sub)
        # get project
        Projects.get(project)
        # get jobs

        if search_term or job_status:
            scan_params = {
                "limit": int(limit),
                "last_evaluated_key": json.loads(last_evaluated_key),
            }

            filter_condition = None

            if search_term:
                filter_condition = ClinicJobs.job_name_lower.contains(
                    search_term.lower()
                )

            if job_status:
                status_condition = ClinicJobs.job_status.contains(job_status)
                if filter_condition is not None:
                    filter_condition = filter_condition & status_condition
                else:
                    filter_condition = status_condition

            jobs = ClinicJobs.scan(
                filter_condition=filter_condition,
                **scan_params,
            )
        else:
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
                "job_name": job.job_name,
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


@router.attach("/dportal/projects/{project}/clinical-workflows/{job_id}/report", "post")
def generate_report(event, context):
    sub = event["requestContext"]["authorizer"]["claims"]["sub"]
    project = event["pathParameters"]["project"]
    job_id = event["pathParameters"]["job_id"]
    body = json.loads(event["body"])

    try:
        # ensure user has access to project
        ProjectUsers.get(project, sub)
        # get project
        Projects.get(project)
        # get variants
        variants = [
            variant
            for entry in ClinicalVariants.query(f"{project}:{job_id}")
            for variant in json.loads(entry.variants)
        ]
    except ProjectUsers.DoesNotExist:
        raise PortalError(404, "User not found in project")
    except Projects.DoesNotExist:
        raise PortalError(404, "Project not found")
    except ClinicalVariants.DoesNotExist:
        raise PortalError(404, "Variants collection not found")

    try:
        if HUB_NAME not in ["RSCM", "RSPON"]:
            response = {
                "success": False,
                "message": "Lab not configured. Please contact administrator.",
            }
            raise KeyError("Lab not configured")
        if not variants:
            payload = {
                "lab": HUB_NAME,
                "kind": "neg",
            }
        else:
            payload = {
                "lab": HUB_NAME,
                "kind": "pos",
                "variants": variants,
            }
        response = invoke_lambda_function(REPORTS_LAMBDA, payload)
        response = {
            "success": True,
            "content": response["body"],
        }
    except KeyError:
        print("Error invoking lambda function: missing key")
        response = {
            "success": False,
            "message": "Lab not configured. Please contact administrator.",
        }
    except Exception as e:
        print(f"Error invoking lambda function: {e}")
        response = {
            "success": False,
            "message": "Error generating report",
        }
    finally:
        return response
