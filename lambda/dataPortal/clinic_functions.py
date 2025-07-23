import os
import json
from datetime import datetime, timezone

from shared.apiutils import LambdaRouter, PortalError
from utils.models import (
    Projects,
    ProjectUsers,
    ClinicJobs,
    ClinicalAnnotations,
    ClinicalVariants,
)
from utils.s3_util import list_s3_prefix, delete_s3_objects
from utils.cognito import get_user_from_attribute, get_user_attribute
from utils.lambda_util import invoke_lambda_function

router = LambdaRouter()
DPORTAL_BUCKET = os.environ.get("DPORTAL_BUCKET")
CLINIC_TEMP_BUCKET_NAMES = os.environ.get("CLINIC_TEMP_BUCKET_NAMES").split(",")
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
        common_params = {
            "limit": int(limit),
            "last_evaluated_key": json.loads(last_evaluated_key),
        }
        if search_term or job_status:
            filter_condition = ClinicJobs.project_name == project
            if search_term:
                filter_condition &= ClinicJobs.job_name_lower.contains(
                    search_term.lower()
                )
            if job_status:
                filter_condition &= ClinicJobs.job_status.contains(job_status)
            jobs = ClinicJobs.scan(
                filter_condition=filter_condition,
                **common_params,
            )
        else:
            jobs = ClinicJobs.project_index.query(
                project,
                **common_params,
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
                "created_at": job.created_at,
            }
            for job in jobs
        ],
        "last_evaluated_key": (
            json.dumps(jobs.last_evaluated_key) if jobs.last_evaluated_key else None
        ),
    }


@router.attach(
    "/dportal/projects/{project}/clinical-workflows/{job_id}",
    "get",
)
def get_job(event, context):
    selected_job = event["pathParameters"]["job_id"]
    project_name = event["pathParameters"]["project"]
    sub = event["requestContext"]["authorizer"]["claims"]["sub"]

    try:
        # check is user registered in project
        ProjectUsers.get(project_name, sub)

        job = ClinicJobs.get(selected_job)
        if job.job_status.lower() in ["failed", "expired"]:
            return {
                "success": False,
                "message": f"Job {selected_job} is a failed/expired status.",
            }
        entry = dict()
        entry["job_id"] = job.job_id
        entry["job_name"] = job.job_name
        entry["validatedByMedicalDirector"] = job.validatedByMedicalDirector or False
        entry["validationComment"] = job.validationComment or ""
        entry["validatedAt"] = job.validatedAt or None

        if job.validatedByMedicalDirector:
            user = get_user_from_attribute("sub", job.validatorSub)
            entry["validator"] = {
                "firstName": get_user_attribute(user, "given_name"),
                "lastName": get_user_attribute(user, "family_name"),
                "email": get_user_attribute(user, "email"),
            }

        return {"success": True, "job": entry}
    except ClinicJobs.DoesNotExist:
        return {
            "success": False,
            "message": f"Job with ID {selected_job} not found",
        }
    except ProjectUsers.DoesNotExist:
        return {
            "success": False,
            "message": "User not registered in project.",
        }


@router.attach(
    "/dportal/projects/{project}/clinical-workflows/{job_id}",
    "delete",
)
def delete_jobid(event, context):
    selected_job = event["pathParameters"]["job_id"]
    project_name = event["pathParameters"]["project"]
    sub = event["requestContext"]["authorizer"]["claims"]["sub"]

    try:
        # check is user registered in project
        ProjectUsers.get(project_name, sub)

        job = ClinicJobs.get(selected_job)
        if job.job_status.lower() in ["failed", "expired"]:
            return {
                "success": False,
                "message": f"Job {selected_job} is a failed/expired status.",
            }
        job.delete()

        # delete files from temp buckets
        for bucket in CLINIC_TEMP_BUCKET_NAMES:
            keys = list_s3_prefix(bucket, selected_job)
            delete_s3_objects(bucket, keys)

    except ClinicJobs.DoesNotExist:
        return {
            "success": False,
            "message": f"Job with ID {selected_job} not found",
        }
    except ProjectUsers.DoesNotExist:
        return {
            "success": False,
            "message": "User not registered in project.",
        }

    return {
        "success": True,
        "message": f"Deleted job {selected_job} from project {project_name}",
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
        variants_annotations = [[] for _ in variants]
        annotations = ClinicalAnnotations.query(f"{project}:{job_id}")

        for annot in annotations:
            annotated_variants = json.loads(annot.variants)
            for idx, var in enumerate(variants):
                if var in annotated_variants:
                    variants_annotations[idx].append(annot.annotation)
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
            "validatedByMedicalDirector": var.validatedByMedicalDirector,
            "validationComment": var.validationComment,
            "validatedAt": var.validatedAt,
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

            if var.validatedByMedicalDirector:
                user = get_user_from_attribute("sub", var.validatorSub)
                entry["validator"] = {
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


@router.attach(
    "/dportal/projects/{project}/clinical-workflows/{job_id}/variants/{name}/validation",
    "post",
)
def validate_variants(event, context):
    sub = event["requestContext"]["authorizer"]["claims"]["sub"]
    is_medical_director = (
        event["requestContext"]["authorizer"]["claims"].get(
            "custom:is_medical_director", "false"
        )
        == "true"
    )

    if not is_medical_director:
        raise PortalError(403, "User is not a medical director")

    body = json.loads(event["body"])
    project = event["pathParameters"]["project"]
    job_id = event["pathParameters"]["job_id"]
    name = event["pathParameters"]["name"]
    comment = body.get("comment", "")

    try:
        # ensure user has access to project
        ProjectUsers.get(project, sub)
        # get project
        Projects.get(project)
        # get variants
        annot = ClinicalVariants(f"{project}:{job_id}", name)
        annot.update(
            actions=[
                ClinicalVariants.validatedByMedicalDirector.set(True),
                ClinicalVariants.validationComment.set(comment),
                ClinicalVariants.validatedAt.set(datetime.now(timezone.utc)),
                ClinicalVariants.validatorSub.set(sub),
            ]
        )
    except ProjectUsers.DoesNotExist:
        raise PortalError(404, "User not found in project")
    except Projects.DoesNotExist:
        raise PortalError(404, "Project not found")
    except ClinicalVariants.DoesNotExist:
        raise PortalError(404, "Variants collection not found")
    except KeyError:
        raise PortalError(400, "Missing required field")

    return {"success": True, "message": "Variants collection validated"}


@router.attach(
    "/dportal/projects/{project}/clinical-workflows/{job_id}/variants/{name}/validation",
    "delete",
)
def invalidate_variants(event, context):
    sub = event["requestContext"]["authorizer"]["claims"]["sub"]
    is_medical_director = (
        event["requestContext"]["authorizer"]["claims"].get(
            "custom:is_medical_director", "false"
        )
        == "true"
    )

    if is_medical_director:
        raise PortalError(403, "User is not a medical director")

    project = event["pathParameters"]["project"]
    job_id = event["pathParameters"]["job_id"]
    name = event["pathParameters"]["name"]

    try:
        # ensure user has access to project
        ProjectUsers.get(project, sub)
        # get project
        Projects.get(project)
        # get variants
        annot = ClinicalVariants(f"{project}:{job_id}", name)
        annot.update(
            actions=[
                ClinicalVariants.validatedByMedicalDirector.set(False),
                ClinicalVariants.validationComment.remove(),
                ClinicalVariants.validatedAt.remove(),
                ClinicalVariants.validatorSub.remove(),
            ]
        )
    except ProjectUsers.DoesNotExist:
        raise PortalError(404, "User not found in project")
    except Projects.DoesNotExist:
        raise PortalError(404, "Project not found")
    except ClinicalVariants.DoesNotExist:
        raise PortalError(404, "Variants collection not found")
    except KeyError:
        raise PortalError(400, "Missing required field")

    return {"success": True, "message": "Variants collection unvalidated"}


@router.attach(
    "/dportal/projects/{project}/clinical-workflows/{job_id}/validation",
    "post",
)
def validate_job_for_negative_reporting(event, context):
    sub = event["requestContext"]["authorizer"]["claims"]["sub"]
    is_medical_director = (
        event["requestContext"]["authorizer"]["claims"].get(
            "custom:is_medical_director", "false"
        )
        == "true"
    )

    if not is_medical_director:
        raise PortalError(403, "User is not a medical director")

    body = json.loads(event["body"])
    project = event["pathParameters"]["project"]
    job_id = event["pathParameters"]["job_id"]
    comment = body.get("comment", "")

    try:
        # check is user registered in project
        ProjectUsers.get(project, sub)
        job = ClinicJobs.get(job_id)
        job.update(
            actions=[
                ClinicJobs.validatedByMedicalDirector.set(True),
                ClinicJobs.validationComment.set(comment),
                ClinicJobs.validatedAt.set(datetime.now(timezone.utc)),
                ClinicJobs.validatorSub.set(sub),
            ]
        )

    except ClinicJobs.DoesNotExist:
        return {
            "success": False,
            "message": f"Job not found",
        }
    except ProjectUsers.DoesNotExist:
        return {
            "success": False,
            "message": "User not registered in project.",
        }

    return {
        "success": True,
        "message": f"Validated job for negative reporting",
    }


@router.attach(
    "/dportal/projects/{project}/clinical-workflows/{job_id}/validation",
    "delete",
)
def invalidate_job_for_negative_reporting(event, context):
    sub = event["requestContext"]["authorizer"]["claims"]["sub"]
    is_medical_director = (
        event["requestContext"]["authorizer"]["claims"].get(
            "custom:is_medical_director", "false"
        )
        == "true"
    )

    if not is_medical_director:
        raise PortalError(403, "User is not a medical director")

    project = event["pathParameters"]["project"]
    job_id = event["pathParameters"]["job_id"]

    try:
        # check is user registered in project
        ProjectUsers.get(project, sub)
        job = ClinicJobs.get(job_id)
        job.update(
            actions=[
                ClinicJobs.validatedByMedicalDirector.set(False),
                ClinicJobs.validationComment.remove(),
                ClinicJobs.validatedAt.remove(),
                ClinicJobs.validatorSub.remove(),
            ]
        )

    except ClinicJobs.DoesNotExist:
        return {
            "success": False,
            "message": f"Job not found",
        }
    except ProjectUsers.DoesNotExist:
        return {
            "success": False,
            "message": "User not registered in project.",
        }

    return {
        "success": True,
        "message": f"Invalidated job for negative reporting",
    }


@router.attach("/dportal/projects/{project}/clinical-workflows/{job_id}/report", "post")
def generate_report(event, context):
    print(f"Generating report for lab: {HUB_NAME}")
    sub = event["requestContext"]["authorizer"]["claims"]["sub"]
    project = event["pathParameters"]["project"]
    job_id = event["pathParameters"]["job_id"]
    body = json.loads(event["body"])

    try:
        # get job
        job = ClinicJobs.get(job_id)
        # ensure user has access to project
        ProjectUsers.get(project, sub)
        # get project
        Projects.get(project)
        # get variants
        variants = [
            variant
            for entry in ClinicalVariants.query(f"{project}:{job_id}")
            for variant in json.loads(entry.variants)
            if entry.validatedByMedicalDirector
        ]
        if len(variants) == 0:
            if not job.validatedByMedicalDirector:
                return {
                    "success": False,
                    "message": "Negative report cannot be generated without validation.",
                }
            print("Generating report with no variants")
        else:
            print(f"Generating report with {len(variants)} variants")
        versions = {
            k: v
            for k, v in job.reference_versions.as_dict().items()
            if k.endswith("_version")
        }
        request_id = event["requestContext"]["requestId"]
        vcf = job.input_vcf
        job_name = job.job_name
    except ProjectUsers.DoesNotExist:
        raise PortalError(404, "User not found in project")
    except ClinicJobs.DoesNotExist:
        raise PortalError(404, "Job not found")
    except Projects.DoesNotExist:
        raise PortalError(404, "Project not found")
    except ClinicalVariants.DoesNotExist:
        raise PortalError(404, "Variants collection not found")

    try:
        if HUB_NAME not in ["RSCM", "RSPON", "RSSARDJITO", "RSJPD", "RSIGNG"]:
            raise KeyError("Lab not configured")
        if HUB_NAME == "RSCM":
            if not variants:
                payload = {
                    "report_id": request_id,
                    "job_id": job_id,
                    "job_name": job_name,
                    "reporter_sub": sub,
                    "project": project,
                    "vcf": vcf,
                    "lab": HUB_NAME,
                    "kind": "neg",
                    "versions": versions,
                }
            else:
                payload = {
                    "report_id": request_id,
                    "job_id": job_id,
                    "job_name": job_name,
                    "reporter_sub": sub,
                    "project": project,
                    "vcf": vcf,
                    "lab": HUB_NAME,
                    "kind": "pos",
                    "variants": variants,
                    "versions": versions,
                }
            response = invoke_lambda_function(REPORTS_LAMBDA, payload)
            return {
                "success": True,
                "content": response["body"],
            }
        elif HUB_NAME == "RSPON":
            if not variants:
                return {
                    "success": False,
                    "message": "Report cannot be generated without variants",
                }
            else:
                # phenotype validation
                phenotype = ",".join((variants[0]["Phenotypes"]))
                if phenotype not in [
                    "Normal Metabolizer",
                    "Intermediate Metabolizer",
                    "Poor Metabolizer",
                    "Rapid Metabolizer",
                ]:
                    return {
                        "success": False,
                        "message": "Invalid phenotype",
                    }
                for ph in variants[1:]:
                    if ",".join((ph["Phenotypes"])) != phenotype:
                        return {
                            "success": False,
                            "message": "Phenotype mismatch",
                        }

                payload = {
                    "report_id": request_id,
                    "job_id": job_id,
                    "job_name": job_name,
                    "reporter_sub": sub,
                    "project": project,
                    "vcf": vcf,
                    "lab": HUB_NAME,
                    "phenotype": phenotype,
                    "alleles": ",".join((variants[0]["Alleles"])),
                    "versions": versions,
                }
            response = invoke_lambda_function(REPORTS_LAMBDA, payload)
            return {
                "success": True,
                "content": response["body"],
            }
        elif HUB_NAME == "RSJPD":
            try:
                # validations
                if len(list(filter(lambda x: x["Gene"] == "SLCO1B1", variants))) > 1:
                    print(
                        "SLCO1B1 gene not found or multiple entries found in variants"
                    )
                    return {
                        "success": False,
                        "message": "SLCO1B1 gene must be present at most once.",
                    }
                if len(list(filter(lambda x: x["Gene"] == "APOE", variants))) > 1:
                    print("APOE gene not found or multiple entries found in variants")
                    return {
                        "success": False,
                        "message": "APOE gene must be present at most once.",
                    }
                slco1b1_variant = [v for v in variants if v["Gene"] == "SLCO1B1"]
                if slco1b1_variant:
                    slco1b1_variant = slco1b1_variant[0]  # Get the first match
                    slco1b1 = {
                        "diplotype": ",".join(slco1b1_variant["Alleles"]),
                        "phenotype": ",".join(slco1b1_variant["Phenotypes"]),
                        "genotype": ",".join(slco1b1_variant["Zygosity"]),
                    }
                else:
                    slco1b1 = {
                        "diplotype": "-",
                        "phenotype": "-",
                        "genotype": "-",
                    }
                apoe_variant = [v for v in variants if v["Gene"] == "APOE"]
                if apoe_variant:
                    apoe_variant = apoe_variant[0]  # Get the first match
                    apoe = {
                        "diplotype": apoe_variant["Alleles"],
                        "phenotype": apoe_variant["Phenotype Categories"],
                        "genotype": apoe_variant["Zygosity"],
                    }
                else:
                    apoe = {
                        "diplotype": "-",
                        "phenotype": "-",
                        "genotype": "-",
                    }
                payload = {
                    "report_id": request_id,
                    "job_id": job_id,
                    "job_name": job_name,
                    "reporter_sub": sub,
                    "project": project,
                    "vcf": vcf,
                    "lab": HUB_NAME,
                    "slco1b1": slco1b1,
                    "apoe": apoe,
                    "versions": versions,
                }
                response = invoke_lambda_function(REPORTS_LAMBDA, payload)
                return {
                    "success": True,
                    "content": response["body"],
                }
            except Exception as e:
                print(f"Error processing variant: {e}")
                return {
                    "success": False,
                    "message": "Invalid data in selection.",
                }
        elif HUB_NAME == "RSIGNG":
            payload = {
                "report_id": request_id,
                "job_id": job_id,
                "job_name": job_name,
                "reporter_sub": sub,
                "project": project,
                "vcf": vcf,
                "lab": HUB_NAME,
                "variants": variants,
                "versions": versions,
            }
            response = invoke_lambda_function(REPORTS_LAMBDA, payload)
            return {
                "success": True,
                "content": response["body"],
            }
        elif HUB_NAME == "RSSARDJITO":
            if not variants:
                payload = {
                    "report_id": request_id,
                    "job_id": job_id,
                    "job_name": job_name,
                    "reporter_sub": sub,
                    "project": project,
                    "vcf": vcf,
                    "lab": HUB_NAME,
                    "kind": "neg",
                    "lang": body["lang"],
                    "mode": body["mode"],
                    "versions": versions,
                }
            else:
                payload = {
                    "report_id": request_id,
                    "job_id": job_id,
                    "job_name": job_name,
                    "reporter_sub": sub,
                    "project": project,
                    "vcf": vcf,
                    "lab": HUB_NAME,
                    "kind": "pos",
                    "lang": body["lang"],
                    "mode": body["mode"],
                    "variants": variants,
                    "versions": versions,
                }
            response = invoke_lambda_function(REPORTS_LAMBDA, payload)
            return {
                "success": True,
                "content": response["body"],
            }
        else:
            return {
                "success": False,
                "message": "Lab is not ready for reporting.",
            }
    except KeyError as e:
        print(f"Error invoking lambda function: missing key: {e}")
        return {
            "success": False,
            "message": "Lab not configured. Please contact administrator.",
        }
    except Exception as e:
        print(f"Error invoking lambda function: {e}")
        return {
            "success": False,
            "message": "Error generating report",
        }
