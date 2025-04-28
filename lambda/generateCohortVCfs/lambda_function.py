import json
import os

from smart_open import open as sopen

from shared.apiutils import parse_request

from metadata_utils import gather_metadata, extract_vcfs
from utils import get_user_identity

DPORTAL_BUCKET = os.environ["DPORTAL_BUCKET"]


def lambda_handler(event, context):
    print("Backend Event Received: {}".format(json.dumps(event)))
    sub = event["sub"]
    job_id = event["jobId"]
    scope = event["scope"]
    query_event = {
        "httpMethod": "POST",
        "requestContext": {
            "authorizer": {"claims": {"sub": sub}},
        },
        "body": json.dumps(
            {
                "projects": event["projects"],
                "query": event["query"],
                "meta": {"apiVersion": "v2.0"},
            }
        ),
    }

    request_params, errors, status = parse_request(query_event)

    if errors:
        return {"success": False, "errors": errors}

    sub = request_params.sub
    identity_id = get_user_identity(sub)
    job_path = f"s3://{DPORTAL_BUCKET}/private/{identity_id}/cohorts/{job_id}"

    try:
        with sopen(f"{job_path}/status.json", "w") as f:
            json.dump({"status": "running"}, f)
        if scope == "individuals":
            print("Extraction using individuals")
            metadata_file_path = gather_metadata(request_params)
            print("Metadata file name: ", metadata_file_path)
            extract_vcfs(job_path, metadata_file_path)
            print("Extracted VCFs")
        if scope == "g_variants":
            print("Extraction using g_variants")
            metadata_file_path = gather_metadata(request_params)
            print("Metadata file name: ", metadata_file_path)
            extract_vcfs(
                job_path, metadata_file_path, request_params.query.request_parameters
            )
            print("Extracted VCFs")
        with sopen(f"{job_path}/status.json", "w") as f:
            json.dump({"status": "completed"}, f)
    except Exception as e:
        print("Error", str(e))
        with sopen(f"{job_path}/status.json", "w") as f:
            json.dump({"status": "failed", "message": str(e)}, f)


if __name__ == "__main__":
    # example 1
    event = {
        "jobId": "test_ind_cohort",
        "sub": "f98e24c8-2011-70ae-9d93-084eb3f4b282",
        "projects": ["Example Query Project"],
        "scope": "individuals",
        "query": {"filters": [], "requestedGranularity": "record"},
        "meta": {"apiVersion": "v2.0"},
    }
    # example 2
    # event = {
    #     "jobId": "test_var_cohort",
    #     "projects": ["Example Query Project"],
    #     "scope": "g_variants",
    #     "sub": "f98e24c8-2011-70ae-9d93-084eb3f4b282",
    #     "query": {
    #         "filters": [],
    #         "requestedGranularity": "record",
    #         "requestParameters": {
    #             "assemblyId": "GRCH38",
    #             "start": ["546801"],
    #             "end": ["546810"],
    #             "referenceName": "1",
    #             "referenceBases": "N",
    #             "alternateBases": "N",
    #         },
    #     },
    #     "meta": {"apiVersion": "v2.0"},
    # }

    lambda_handler(event, None)
