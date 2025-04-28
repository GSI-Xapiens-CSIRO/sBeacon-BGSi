import argparse
import json

import boto3

from common import anonymise, GENOMIC_SUFFIX_TYPES, WORKING_DIR
from file_validation import validate_file
from metadata_deidentification import (
    anonymise_json,
    anonymise_tabular,
    anonymise_txt,
)
from genomic_deidentification import (
    anonymise_bam,
    anonymise_sam,
    anonymise_vcf,
    ProcessError,
    ParsingError,
)


SAM_SUFFIXES = {
    ".bam",
    ".sam",
}

QUIETLY_SKIP_SUFFIXES = {
    # Because we'll be creating these ourselves
    # from other files, and don't want the uploaded
    # versions to squash the ones we create.
    ".bai",
    ".csi",
}

METADATA_SUFFIXES = [
    ".json",
    ".csv",
    ".tsv",
    ".txt",
]

dynamodb = boto3.client("dynamodb")
s3 = boto3.client("s3")


def dynamodb_update_item(table_name, location, update_fields: dict):
    update_expression = "SET " + ", ".join(f"{k} = :{k}" for k in update_fields.keys())
    if "error_message" not in update_fields:
        update_expression += " REMOVE error_message"
    kwargs = {
        "TableName": table_name,
        "Key": {
            "vcfLocation": {"S": location},
        },
        "UpdateExpression": update_expression,
        "ExpressionAttributeValues": {f":{k}": v for k, v in update_fields.items()},
    }
    print(f"Calling dynamodb.update_item with kwargs: {json.dumps(kwargs)}")
    response = dynamodb.update_item(**kwargs)
    print(f"Received response: {json.dumps(response, default=str)}")


def update_deidentification_status(files_table, location, status):
    update_fields = {
        "deidentificationStatus": {
            "S": status,
        }
    }
    dynamodb_update_item(files_table, location, update_fields)


def log_error(files_table, location, error_message):
    update_fields = {
        "deidentificationStatus": {
            "S": "Error",
        },
        "error_message": {
            "S": error_message,
        },
    }
    dynamodb_update_item(files_table, location, update_fields)


def log_projects_error(
    projects_table: str, project_name: str, file_name: str, error_message: str
):
    update_expression = """
    SET error_messages = list_append(if_not_exists(error_messages, :empty_list), :error_message)
    DELETE files :file_name
    """
    kwargs = {
        "TableName": projects_table,
        "Key": {
            "name": {"S": project_name},
        },
        "UpdateExpression": update_expression,
        "ExpressionAttributeValues": {
            ":error_message": {
                "L": [
                    {
                        "M": {
                            "file": {"S": file_name},
                            "error": {"S": error_message},
                        }
                    }
                ]
            },
            ":empty_list": {"L": []},
            ":file_name": {"SS": [file_name]},
        },
    }
    print(f"Calling dynamodb.update_item with kwargs: {json.dumps(kwargs)}")
    response = dynamodb.update_item(**kwargs)
    print(f"Received response: {json.dumps(response, default=str)}")


def s3_download(**kwargs: dict):
    print(f"Calling s3.download_file with kwargs: {json.dumps(kwargs)}")
    response = s3.download_file(**kwargs)
    print(f"Received response: {json.dumps(response, default=str)}")


def s3_upload(**kwargs: dict):
    print(f"Calling s3.upload_file with kwargs: {json.dumps(kwargs)}")
    response = s3.upload_file(**kwargs)
    print(f"Received response: {json.dumps(response, default=str)}")


def deidentify(
    input_bucket,
    output_bucket,
    projects_table,
    files_table,
    project,
    file_name,
    object_key,
):
    update_deidentification_status(
        files_table, f"{project}/project-files/{file_name}", "Pending"
    )

    local_input_path = f"{WORKING_DIR}/input_{file_name}"
    local_output_path = f"{WORKING_DIR}/deidentified_{file_name}"

    s3.download_file(Bucket=input_bucket, Key=object_key, Filename=local_input_path)

    try:
        validate_file(local_input_path)
        print(f"Validation passed for {local_input_path}")
    except Exception as e:
        print(f"An error occurred when validating {object_key}: {e}")
        log_error(files_table, f"{project}/project-files/{file_name}", str(e))
        log_projects_error(projects_table, project, file_name, anonymise(str(e)))
        s3.delete_object(Bucket=input_bucket, Key=object_key)
        print("Exiting")
        return
    if any(
        object_key.endswith(suffix)
        for suffix in set(GENOMIC_SUFFIX_TYPES.keys()) | SAM_SUFFIXES
    ):
        try:
            if any(object_key.endswith(suffix) for suffix in SAM_SUFFIXES):
                if object_key.endswith(".bam"):
                    output_paths = anonymise_bam(local_input_path, local_output_path)
                elif object_key.endswith(".sam"):
                    output_paths = anonymise_sam(local_input_path, local_output_path)
                else:
                    raise (Exception("Unexpected SAM file suffix"))
            else:
                output_paths = anonymise_vcf(local_input_path, local_output_path)
        except (ProcessError, ParsingError) as e:
            print(f"An error occurred while deidentifying {object_key}: {e}")
            log_error(files_table, f"{project}/project-files/{file_name}", str(e))
            log_projects_error(projects_table, project, file_name, anonymise(str(e)))
            s3.delete_object(Bucket=input_bucket, Key=object_key)
            print("Exiting")
            return
    elif any(object_key.endswith(suffix) for suffix in QUIETLY_SKIP_SUFFIXES):
        print("We'd rather create this file again from the source file, skipping")
        return
    elif any(object_key.endswith(suffix) for suffix in METADATA_SUFFIXES):
        try:
            if object_key.endswith(".json"):
                anonymise_json(local_input_path, local_output_path)
            elif object_key.endswith(".csv"):
                anonymise_tabular(local_input_path, local_output_path, delimiter=",")
            elif object_key.endswith(".tsv"):
                anonymise_tabular(local_input_path, local_output_path, delimiter="\t")
            elif object_key.endswith(".txt"):
                anonymise_txt(local_input_path, local_output_path)
        except Exception as e:
            print(f"An error occurred while deidentifying {object_key}: {e}")
            log_error(files_table, f"{project}/project-files/{file_name}", str(e))
            log_projects_error(projects_table, project, file_name, anonymise(str(e)))
            s3.delete_object(Bucket=input_bucket, Key=object_key)
            print("Exiting")
            return
        output_paths = [local_output_path]
    else:
        raise ValueError(f"File {object_key} does not have a recognised suffix")

    output_key = object_key.split("/", 1)[1]
    base_path = output_paths[0]
    s3.upload_file(Bucket=output_bucket, Key=output_key, Filename=output_paths[0])
    for extra_file in output_paths[1:]:
        assert extra_file.startswith(
            base_path
        ), f"Extra file {extra_file} does not match output path {base_path}"
        s3.upload_file(
            Bucket=output_bucket,
            Key=f"{output_key}{extra_file[len(base_path):]}",
            Filename=extra_file,
        )
    s3.delete_object(Bucket=input_bucket, Key=object_key)

    update_deidentification_status(
        files_table, f"{project}/project-files/{file_name}", "Anonymised"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-bucket", required=True)
    parser.add_argument("--output-bucket", required=True)
    parser.add_argument("--projects-table", required=True)
    parser.add_argument("--files-table", required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--file-name", required=True)
    parser.add_argument("--object-key", required=True)
    args = parser.parse_args()
    print("EC2: Starting logs")
    deidentify(
        args.input_bucket,
        args.output_bucket,
        args.projects_table,
        args.files_table,
        args.project,
        args.file_name,
        args.object_key,
    )
