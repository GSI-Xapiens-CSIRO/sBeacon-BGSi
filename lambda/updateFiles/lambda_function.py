import json
import os
import subprocess
from urllib.parse import unquote_plus

import boto3
from botocore.exceptions import ClientError

DPORTAL_BUCKET = os.environ["DPORTAL_BUCKET"]
PROJECTS_TABLE = os.environ["DYNAMO_PROJECTS_TABLE"]
VCFS_TABLE = os.environ["DYNAMO_VCFS_TABLE"]
JOBS_TABLE = os.environ["DYNAMO_CLINIC_JOBS_TABLE"]
JOBS_TABLE_PROJECT_NAME_INDEX = os.environ["DYNAMO_CLINIC_JOBS_PROJECT_NAME_INDEX"]
VCF_SUFFIXES = [
    ".bcf",
    ".bcf.gz",
    ".bcf.bgz",
    ".vcf",
    ".vcf.gz",
    ".vcf.bgz",
]

dynamodb = boto3.client("dynamodb")
s3 = boto3.client("s3")


def count_samples_and_update_vcf(vcf_location):
    try:
        num_samples = count_samples(f"s3://{DPORTAL_BUCKET}/projects/{vcf_location}")
        update_fields = {
            "num_samples": {
                "N": str(num_samples),
            },
        }
    except subprocess.CalledProcessError as e:
        print(f"Error counting samples for {vcf_location}: {e.__dict__}")
        num_samples = 0
        update_fields = {
            "num_samples": {
                "N": str(num_samples),
            },
            "error_message": {"S": e.stderr},
        }
    update_file(vcf_location, update_fields)
    return num_samples


def count_samples(s3_location):
    process_args = ["bcftools", "query", "-l", s3_location]
    print(f"Running process with args: {process_args}")
    query_process = subprocess.run(
        args=process_args,
        capture_output=True,
        check=True,
        cwd="/tmp",
        encoding="ascii",
    )
    num_samples = query_process.stdout.count("\n")
    print(f"Counted {num_samples} samples")
    return num_samples


def get_all_counts(project, all_files):
    vcf_locations = [
        f"{project}/project-files/{file_name}"
        for file_name in all_files
        if any(file_name.endswith(suffix) for suffix in VCF_SUFFIXES)
    ]
    locations_to_check = set(vcf_locations)
    print(f"Adding the samples across {len(locations_to_check)} files")
    print(f"Checking the following files: {vcf_locations}")
    total_samples = 0
    while locations_to_check:
        kwargs = {
            "RequestItems": {
                VCFS_TABLE: {
                    "Keys": [
                        {
                            "vcfLocation": {
                                "S": vcf_location,
                            },
                        }
                        for vcf_location in vcf_locations[:100]
                    ],
                    "ConsistentRead": True,
                    "ProjectionExpression": "vcfLocation,num_samples",
                },
            },
        }
        print(f"Calling dynamodb.batch_get_item with kwargs: {json.dumps(kwargs)}")
        response = dynamodb.batch_get_item(**kwargs)
        print(f"Received response: {json.dumps(response, default=str)}")
        items = response.get("Responses", {}).get(VCFS_TABLE, [])

        # handling error when the num_samples is absent
        try:
            total_samples += sum(int(item["num_samples"]["N"]) for item in items)
        except KeyError:
            total_samples += 0

        locations_to_check -= {item["vcfLocation"]["S"] for item in items}
        vcf_locations = [
            location["vcfLocation"]["S"]
            for location in response.get("UnprocessedKeys", {}).get(VCFS_TABLE, [])
        ] + vcf_locations[100:]
        missing_locations = locations_to_check - set(vcf_locations)
        if missing_locations:
            print(
                f"At least the following files do not have sample counts: {missing_locations}"
            )
            # Some items are yet to be added to the table, a later invocation will try again
            return -1
    print(f"Found a total of {total_samples} samples")
    return total_samples


def get_all_project_files(project_prefix):
    # TODO verify that this operation is absolutely necesarry on staging files
    prefixes = [project_prefix, f"staging/{project_prefix}"]
    all_files = set()
    for prefix in prefixes:
        kwargs = {
            "Bucket": DPORTAL_BUCKET,
            "Prefix": prefix,
        }
        prefix_length = len(prefix)
        remaining_files = True
        while remaining_files:
            print(f"Calling s3.list_objects_v2 with kwargs: {json.dumps(kwargs)}")
            response = s3.list_objects_v2(**kwargs)
            print(f"Received response: {json.dumps(response, default=str)}")
            all_files.update(
                [
                    obj["Key"][prefix_length:]
                    for obj in response.get("Contents", [])
                    if obj["Key"][-1] != "/"
                ]
            )
            remaining_files = response.get("IsTruncated", False)
            if remaining_files:
                kwargs["ContinuationToken"] = response["NextContinuationToken"]
    return list(all_files)


def get_project(object_key):
    path_parts = object_key.split("/")
    # Ensure the path starts with "projects/"
    if path_parts[0] != "projects":
        error = (
            "Not triggered by a projects/* file. This shouldn't happen."
            " Check the function trigger."
        )
        print(error)
        raise ValueError(error)
    # Ensure the path has at least 4 parts: "projects/{project}/project-files/{filename}"
    if len(path_parts) < 4:
        return None, None, None  # Not in a project directory
    # Ensure the second part (project name) is present
    project_name = path_parts[1]
    if not project_name:
        return None, None, None  # Invalid project name
    # Ensure the third part is exactly "project-files"
    if path_parts[2] != "project-files":
        return None, None, None  # Not inside the "project-files" directory
    # Ensure this is a file (not a directory)
    if object_key.endswith("/"):
        return None, None, None  # It's a directory, not a file
    # Return project name, the base project path, and the filename
    return (
        project_name,
        f"projects/{project_name}/project-files/",
        "/".join(path_parts[3:]),
    )


def refresh_project(project_name):
    """This should only be needed if something has gone wrong"""
    print(f"Refreshing project: {project_name}")
    all_project_files = get_all_project_files(f"projects/{project_name}/project-files/")
    total_samples = 0
    for file_name in all_project_files:
        if any(file_name.endswith(suffix) for suffix in VCF_SUFFIXES):
            total_samples += count_samples_and_update_vcf(project_name, file_name)
    update_project(project_name, total_samples, all_project_files)


def remove_vcf(vcf_location):
    kwargs = {
        "TableName": VCFS_TABLE,
        "Key": {
            "vcfLocation": {
                "S": vcf_location,
            },
        },
    }
    print(f"Calling dynamodb.delete_item with kwargs: {json.dumps(kwargs)}")
    response = dynamodb.delete_item(**kwargs)
    print(f"Received response: {json.dumps(response, default=str)}")


def update_project(project_name, total_samples, all_project_files):
    kwargs = {
        "TableName": PROJECTS_TABLE,
        "Key": {
            "name": {
                "S": project_name,
            },
        },
        "UpdateExpression": "SET total_samples=:total_samples",
        "ConditionExpression": "attribute_exists(#name)",
        "ExpressionAttributeNames": {
            "#name": "name",
        },
        "ExpressionAttributeValues": {
            ":total_samples": {
                "N": str(total_samples),
            },
        },
    }
    if all_project_files:
        kwargs["UpdateExpression"] += ", files=:files"
        kwargs["ExpressionAttributeValues"][":files"] = {
            "SS": all_project_files,
        }
    else:
        kwargs["UpdateExpression"] += " REMOVE files"
    print(f"Calling dynamodb.update_item with kwargs: {json.dumps(kwargs)}")
    try:
        response = dynamodb.update_item(**kwargs)
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            print("Project doesn't exist, aborting")
            return
        else:
            print(
                f"Received unexpected ClientError: {json.dumps(e.response, default=str)}"
            )
            raise e
    print(f"Received response: {json.dumps(response, default=str)}")


def expire_clinic_jobs(project, file_name):
    print(
        f"Attempting to delete all jobs associated with project {project} and file {file_name}"
    )
    kwargs = {
        "TableName": JOBS_TABLE,
        "IndexName": JOBS_TABLE_PROJECT_NAME_INDEX,
        "KeyConditionExpression": "project_name = :project_name",
        "ExpressionAttributeValues": {
            ":project_name": {
                "S": project,
            },
        },
    }
    print(f"Calling dynamodb.query with kwargs: {json.dumps(kwargs)}")
    response = dynamodb.query(**kwargs)
    print(f"Received response: {json.dumps(response)}")
    if "Items" not in response:
        print(f"No associated jobs found, aborting")
        return
    jobs_to_expire = [
        job
        for job in response["Items"]
        if job.get("input_vcf", {}).get("S") == file_name
    ]

    updated_count = 0
    error_count = 0
    for job in jobs_to_expire:
        job_id = job.get("job_id", {}).get("S")
        if job_id:
            kwargs = {
                "TableName": JOBS_TABLE,
                "Key": {
                    "job_id": {"S": job_id},
                },
                "UpdateExpression": "SET job_status = :job_status",
                "ExpressionAttributeValues": {
                    ":job_status": {
                        "S": "expired",
                    },
                },
                "ConditionExpression": "attribute_exists(job_id)",
            }
            print(f"Calling dynamodb.update_item with kwargs: {json.dumps(kwargs)}")
            try:
                response = dynamodb.update_item(**kwargs)
                print(f"Received response: {json.dumps(response)}")
                updated_count += 1
            except ClientError as e:
                print(f"Error updating job {job_id}: {e}")
                error_count += 1
        else:
            print(f"Missing job_id for a job, skipping")

    print(
        f"Job expiration complete. Updated: {updated_count}, Errors: {error_count}, Skipped: {len(jobs_to_expire) - updated_count - error_count}"
    )


def update_file(location, update_fields):
    update_expression = "SET " + ", ".join(f"{k} = :{k}" for k in update_fields.keys())
    expression_attribute_values = {f":{k}": v for k, v in update_fields.items()}

    kwargs = {
        "TableName": VCFS_TABLE,
        "Key": {
            "vcfLocation": {"S": location},
        },
        "UpdateExpression": update_expression,
        "ExpressionAttributeValues": expression_attribute_values,
    }

    print(f"Calling dynamodb.update_item with kwargs: {json.dumps(kwargs)}")
    response = dynamodb.update_item(**kwargs)
    print(f"Received response: {json.dumps(response, default=str)}")


def lambda_handler(event, context):
    print(f"Backend Event Received: {json.dumps(event)}")
    if project_name := event.get("project"):
        refresh_project(project_name)
        return
    bucket_name = event["Records"][0]["s3"]["bucket"]["name"]
    assert (
        bucket_name == DPORTAL_BUCKET
    ), f"Unexpected bucket: {bucket_name}, should be {DPORTAL_BUCKET}"
    object_key = unquote_plus(event["Records"][0]["s3"]["object"]["key"])
    event_name = event["Records"][0]["eventName"]
    project, project_prefix, file_name = get_project(object_key)
    if project is None:
        print("Not a projects/<project_name>/project-files/* file, skipping")
        return
    if any(object_key.endswith(suffix) for suffix in VCF_SUFFIXES):
        vcf_location = f"{project}/project-files/{file_name}"
        if event_name.startswith("ObjectCreated:"):
            count_samples_and_update_vcf(vcf_location)
        elif event_name.startswith("ObjectRemoved:"):
            remove_vcf(vcf_location)
            expire_clinic_jobs(project, file_name)
        else:
            print(f"Unexpected event name: {event_name}")
            raise ValueError(f"Unexpected event name: {event_name}")
    else:
        print("Not a gzipped BCF/VCF, not counting samples")
    all_project_files = get_all_project_files(project_prefix)
    total_samples = get_all_counts(project, all_project_files)
    if total_samples < 0:
        print("Not all samples have been counted yet, leaving for another invocation")
        return
    update_project(project, total_samples, all_project_files)
