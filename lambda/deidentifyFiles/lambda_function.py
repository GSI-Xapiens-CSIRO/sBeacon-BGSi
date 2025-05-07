import json
import os
from urllib.parse import unquote_plus

import boto3
from botocore.exceptions import ClientError

from deidentification import deidentify, log_deidentification_status
from launch_ec2 import launch_deidentification_ec2

dynamodb = boto3.client("dynamodb")
s3 = boto3.client("s3")

DPORTAL_BUCKET = os.environ["DPORTAL_BUCKET"]
PROJECTS_TABLE = os.environ["DYNAMO_PROJECTS_TABLE"]
FILES_TABLE = os.environ["DYNAMO_VCFS_TABLE"]
MAX_SIZE_FOR_LAMBDA = 1024**3  # 1 GB
SUFFIXES = [
    ".bam",
    ".sam",
    ".bcf",
    ".bcf.gz",
    ".bcf.bgz",
    ".vcf",
    ".vcf.gz",
    ".vcf.bgz",
    ".json",
    ".csv",
    ".tsv",
    ".txt",
]
INDEX_SUFFIXES = [
    ".tbi",
    ".csi",
]


def get_all_project_files(project_prefix):
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
    # Ensure the path starts with "staging/projects/"
    if path_parts[0:2] != ["staging", "projects"]:
        error = (
            "Not triggered by a staging/projects/* file. This shouldn't happen."
            " Check the function trigger."
        )
        print(error)
        raise ValueError(error)
    # Ensure the path has at least 5 parts: "staging/projects/{project}/project-files/{filename}"
    if len(path_parts) < 5:
        return None, None, None  # Not in a project directory
    # Ensure the third part (project name) is present
    project_name = path_parts[2]
    if not project_name:
        return None, None, None  # Invalid project name
    # Ensure the fourth part is exactly "project-files"
    if path_parts[3] != "project-files":
        return None, None, None  # Not inside the "project-files" directory
    # Ensure this is a file (not a directory)
    if object_key.endswith("/"):
        return None, None, None  # It's a directory, not a file
    # Return project name, the base project path, and the filename
    return (
        project_name,
        f"{path_parts[1]}/{path_parts[2]}/{path_parts[3]}/",
        "/".join(path_parts[4:]),
    )


def refresh_project(project_name):
    """This should only be needed if something has gone wrong"""
    print(f"Refreshing project: {project_name}")
    all_project_files = get_all_project_files(f"projects/{project_name}/project-files/")
    update_project(project_name, all_project_files)


def update_project(project_name, all_project_files):
    kwargs = {
        "TableName": PROJECTS_TABLE,
        "Key": {
            "name": {
                "S": project_name,
            },
        },
        "UpdateExpression": "SET files=:files",
        "ConditionExpression": "attribute_exists(#name)",
        "ExpressionAttributeNames": {
            "#name": "name",
        },
        "ExpressionAttributeValues": {
            ":files": {
                "SS": all_project_files,
            },
        },
    }
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


def update_file(location, update_fields):
    update_expression = "SET " + ", ".join(f"{k} = :{k}" for k in update_fields.keys())
    expression_attribute_values = {f":{k}": v for k, v in update_fields.items()}

    kwargs = {
        "TableName": FILES_TABLE,
        "Key": {
            "vcfLocation": {"S": location},
        },
        "UpdateExpression": update_expression,
        "ExpressionAttributeValues": expression_attribute_values,
    }

    print(f"Calling dynamodb.update_item with kwargs: {json.dumps(kwargs)}")
    response = dynamodb.update_item(**kwargs)
    print(f"Received response: {json.dumps(response, default=str)}")


def move_file(object_key):
    s3.copy_object(
        Bucket=DPORTAL_BUCKET,
        CopySource={"Bucket": DPORTAL_BUCKET, "Key": object_key},
        Key=object_key.split("/", 1)[1],
    )
    s3.delete_object(Bucket=DPORTAL_BUCKET, Key=object_key)
    return


def remove_file(object_key):
    s3.delete_object(Bucket=DPORTAL_BUCKET, Key=object_key)
    return


def lambda_handler(event, context):
    print(f"Backend Event Received: {json.dumps(event)}")
    input_bucket_name = event["Records"][0]["s3"]["bucket"]["name"]
    assert (
        input_bucket_name == DPORTAL_BUCKET
    ), f"Unexpected input bucket: {input_bucket_name}, should be {DPORTAL_BUCKET}"
    object_key = unquote_plus(event["Records"][0]["s3"]["object"]["key"])
    event_name = event["Records"][0]["eventName"]
    project, project_prefix, file_name = get_project(object_key)
    if project is None:
        print("Not a staging/projects/<project_name>/project-files/* file, skipping")
        return
    all_project_files = get_all_project_files(project_prefix)
    update_project(project, all_project_files)
    if event_name.startswith("ObjectCreated:"):
        log_deidentification_status(PROJECTS_TABLE, project, file_name, "Pending")
        if any(object_key.endswith(suffix) for suffix in INDEX_SUFFIXES):
            print(f"{object_key} is an index file, moving directly")
            move_file(object_key)
            log_deidentification_status(PROJECTS_TABLE, project, file_name, "Anonymised")
            return
        else:
            print(f"{object_key} is a genomic or metadata file, deidentifying")
            size = event["Records"][0]["s3"]["object"]["size"]
            if size <= MAX_SIZE_FOR_LAMBDA:
                deidentify(
                    input_bucket=DPORTAL_BUCKET,
                    output_bucket=DPORTAL_BUCKET,
                    projects_table=PROJECTS_TABLE,
                    files_table=FILES_TABLE,
                    project=project,
                    file_name=file_name,
                    object_key=object_key,
                )
            else:
                launch_deidentification_ec2(
                    input_bucket=DPORTAL_BUCKET,
                    output_bucket=DPORTAL_BUCKET,
                    projects_table=PROJECTS_TABLE,
                    files_table=FILES_TABLE,
                    project=project,
                    file_name=file_name,
                    object_key=object_key,
                    size_gb=size / 1024**3,
                )
            return
