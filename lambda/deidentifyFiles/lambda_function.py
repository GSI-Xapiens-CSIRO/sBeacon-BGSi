import json
import os
from urllib.parse import unquote_plus
from time import sleep

import boto3
from botocore.exceptions import ClientError

from deidentification import deidentify
from launch_ec2 import launch_deidentification_ec2

dynamodb = boto3.client("dynamodb")
s3 = boto3.client("s3")

DPORTAL_BUCKET = os.environ["DPORTAL_BUCKET"]
STAGING_BUCKET = os.environ["STAGING_BUCKET"]
PROJECTS_TABLE = os.environ["DYNAMO_PROJECTS_TABLE"]
FILES_TABLE = os.environ["DYNAMO_VCFS_TABLE"]
SUFFIXES = [
    ".bcf",
    ".bcf.gz",
    ".vcf",
    ".vcf.gz",
    ".json",
    ".csv",
    ".tsv",
]

def get_all_project_files(project_prefix):
    kwargs_list = [
        {
            "Bucket": DPORTAL_BUCKET,
            "Prefix": project_prefix,
        },
        {
            "Bucket": STAGING_BUCKET,
            "Prefix": project_prefix,
        }
    ]
    prefix_length = len(project_prefix)
    all_files = set()
    for kwargs in kwargs_list:
        remaining_files = True
        while remaining_files:
            print(f"Calling s3.list_objects_v2 with kwargs: {json.dumps(kwargs)}")
            response = s3.list_objects_v2(**kwargs)
            print(f"Received response: {json.dumps(response, default=str)}")
            all_files.update([obj["Key"][prefix_length:] for obj in response.get("Contents", [])])
            remaining_files = response.get("IsTruncated", False)
            if remaining_files:
                kwargs["ContinuationToken"] = response["NextContinuationToken"]
    return list(all_files)

def get_project(object_key):
    path_parts = object_key.split("/")
    if path_parts[0] != "projects":
        error = (
            "Not triggered by a projects/* file. This shouldn't happen."
            " Check the function trigger."
        )
        print(error)
        raise ValueError(error)
    if len(path_parts) < 3:
        # This is a projects/* file, not a projects/*/* file
        # Therefore it isn't in a project directory
        return None, None, None
    return path_parts[1], f"{path_parts[0]}/{path_parts[1]}/", "/".join(path_parts[2:])

def refresh_project(project_name):
    """This should only be needed if something has gone wrong"""
    print(f"Refreshing project: {project_name}")
    all_project_files = get_all_project_files(f"projects/{project_name}/")
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

def get_project(object_key):
    path_parts = object_key.split("/")
    if path_parts[0] != "projects":
        error = (
            "Not triggered by a projects/* file. This shouldn't happen."
            " Check the function trigger."
        )
        print(error)
        raise ValueError(error)
    if len(path_parts) < 3:
        # This is a projects/* file, not a projects/*/* file
        # Therefore it isn't in a project directory
        return None, None, None
    return path_parts[1], f"{path_parts[0]}/{path_parts[1]}/", "/".join(path_parts[2:])

def move_file(object_key):
    s3.copy_object(
            Bucket=DPORTAL_BUCKET,
            CopySource={'Bucket': STAGING_BUCKET, 'Key': object_key},
            Key=object_key
        )
    s3.delete_object(Bucket=STAGING_BUCKET, Key=object_key)
    return

def remove_file(object_key):
    s3.delete_object(Bucket=STAGING_BUCKET, Key=object_key)
    return

def lambda_handler(event, context):
    print(f"Event Received: {json.dumps(event)}")
    input_bucket_name = event["Records"][0]["s3"]["bucket"]["name"]
    assert (
        input_bucket_name == STAGING_BUCKET
    ), f"Unexpected input bucket: {input_bucket_name}, should be {STAGING_BUCKET}"
    object_key = unquote_plus(event["Records"][0]["s3"]["object"]["key"])
    event_name = event["Records"][0]["eventName"]
    project, project_prefix, file_name = get_project(object_key)
    all_project_files = get_all_project_files(project_prefix)
    update_project(project, all_project_files)
    if project is None:
        print("Not a projects/<project_name>/* file, skipping")
        return
    if event_name.startswith("ObjectCreated:"):
        if not any(object_key.endswith(suffix) for suffix in SUFFIXES):
            print(f"Not a genomic or metadata file: {object_key}")
            move_file(object_key)
            return
        else:
            # TODO: Add conditional statement that runs EC2 if filesize
            # is near or greater than the lambda's ephemeral storage
            if False:
                deidentify(
                    input_bucket=STAGING_BUCKET,
                    output_bucket=DPORTAL_BUCKET,
                    files_table=FILES_TABLE,
                    project=project,
                    file_name=file_name,
                    object_key=object_key,
                )
            else:
                launch_deidentification_ec2(
                    input_bucket=STAGING_BUCKET,
                    output_bucket=DPORTAL_BUCKET,
                    files_table=FILES_TABLE,
                    project=project,
                    file_name=file_name,
                    object_key=object_key,
                )