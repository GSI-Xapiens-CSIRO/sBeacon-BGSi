import json
import os
import subprocess
from urllib.parse import unquote_plus

import boto3
from botocore.exceptions import ClientError


DPORTAL_BUCKET = os.environ["DPORTAL_BUCKET"]
PROJECTS_TABLE = os.environ["DYNAMO_PROJECTS_TABLE"]
VCFS_TABLE = os.environ["DYNAMO_VCFS_TABLE"]
VCF_SUFFIXES = [
    ".bcf",
    ".bcf.gz",
    ".vcf",
    ".vcf.gz",
]

dynamodb = boto3.client("dynamodb")
s3 = boto3.client("s3")


def count_samples_and_update_vcf(project, file_name):
    vcf_location = f"{project}/{file_name}"
    try:
        num_samples = count_samples(f"s3://{DPORTAL_BUCKET}/projects/{vcf_location}")
    except subprocess.CalledProcessError as e:
        print(f"Error counting samples for {vcf_location}: {e.__dict__}")
        update_vcf(vcf_location, 0, error_message=e.stderr)
        return 0
    update_vcf(vcf_location, num_samples)
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
        f"{project}/{file_name}"
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
        total_samples += sum(int(item["num_samples"]["N"]) for item in items)
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
    kwargs = {
        "Bucket": DPORTAL_BUCKET,
        "Prefix": project_prefix,
    }
    prefix_length = len(project_prefix)
    remaining_files = True
    all_files = set()
    while remaining_files:
        print(f"Calling s3.list_objects_v2 with kwargs: {json.dumps(kwargs)}")
        response = s3.list_objects_v2(**kwargs)
        print(f"Received response: {json.dumps(response, default=str)}")
        all_files = [obj["Key"][prefix_length:] for obj in response.get("Contents", [])]
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
            "SS": [
                f"projects/{project_name}/{file_name}"
                for file_name in all_project_files
            ],
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


def update_vcf(vcf_location, num_samples, error_message=None):
    kwargs = {
        "TableName": VCFS_TABLE,
        "Key": {
            "vcfLocation": {
                "S": vcf_location,
            },
        },
        "UpdateExpression": "SET num_samples=:num_samples",
        "ExpressionAttributeValues": {
            ":num_samples": {
                "N": str(num_samples),
            },
        },
    }
    if error_message:
        kwargs["UpdateExpression"] += ", error_message=:error_message"
        kwargs["ExpressionAttributeValues"][":error_message"] = {
            "S": error_message,
        }
    print(f"Calling dynamodb.update_item with kwargs: {json.dumps(kwargs)}")
    response = dynamodb.update_item(**kwargs)
    print(f"Received response: {json.dumps(response, default=str)}")


def lambda_handler(event, context):
    print(f"Event Received: {json.dumps(event)}")
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
        print("Not a projects/<project_name>/* file, skipping")
        return
    if any(object_key.endswith(suffix) for suffix in VCF_SUFFIXES):
        if event_name.startswith("ObjectCreated:"):
            count_samples_and_update_vcf(project, file_name)
        elif event_name.startswith("ObjectRemoved:"):
            remove_vcf(f"{project}/{file_name}")
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
