import boto3
import re
import csv
import os
import argparse

pii_patterns = {
    "email": r"\b[a-zA-Z0-9._%+-]{3,}@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b",
    "phone": r"(?:\+?62|0)8\d{8,11}(?=\W|$)",
    "nik": r"(?<!SNOMED:)\b\d{16}\b",
    "license_plate": r"\b[A-Z]{1,2}\s\d{1,4}\s[A-Z]{1,3}\b",
    "address": r"\b(?:Jl\.|RT\s\d{1,3}|RW\s\d{1,3}|Kecamatan\s\w+|Kabupaten\s\w+)\b",
    "name": r"/\b(?:Dr\.|H\.|Ir\.)?\s?[A-Z][a-z]{2,}\s[A-Z][a-z]+(?:\s[A-Z][a-z]+)*(?:,\s?[A-Z]{2,3})?\b/gm",
}

GENOMIC_SUFFIXES = [
    ".bcf",
    ".bcf.gz",
    ".vcf",
    ".vcf.gz",
]
METADATA_SUFFIXES = [
    ".json",
    ".csv",
    ".tsv",
]

dynamodb = boto3.client("dynamodb")
s3 = boto3.client("s3")

def deidentify_text(line):
    for key, pattern in pii_patterns.items():
        matches = re.findall(pattern, line)
        for match in matches:
            replacement = "**********"
            line = line.replace(match, replacement)
    return line

def process_tabular(input_path, output_path, delimiter):
    """Processes CSV/TSV files to deidentify PII, writing results line-by-line."""
    with open(input_path, "r", newline="", encoding="utf-8") as infile:
        reader = csv.reader(infile, delimiter=delimiter)
        with open(output_path, "w", newline="", encoding="utf-8") as outfile:
            writer = csv.writer(outfile, delimiter=delimiter)
            for row in reader:
                deidentified_row = [deidentify_text(field) for field in row]
                writer.writerow(deidentified_row)

def process_json(input_path, output_path):
    """Processes JSON files to deidentify PII, writing results line-by-line."""
    with open(input_path, "r") as infile, open(output_path, "w") as outfile:
        for line in infile:
            deidentified_line = deidentify_text(line)
            outfile.write(deidentified_line)

def is_lambda():
    """Checks if the script is running in AWS Lambda."""
    return "AWS_LAMBDA_FUNCTION_NAME" in os.environ

def deidentify_metadata(local_input_path, local_output_path):
    """Main function to process file from S3, deidentify, and upload back to S3."""

    if local_input_path.endswith(".json"):
        process_json(local_input_path, local_output_path)
    elif local_input_path.endswith(".csv"):
        process_tabular(local_input_path, local_output_path, delimiter=",")
    elif local_input_path.endswith(".tsv"):
        process_tabular(local_input_path, local_output_path, delimiter="\t")

    return True

def deidentify_genomic():
    return

def update_deidentification_status(files_table, location, status):
    update_fields = {
        "deidentificationStatus": {
            "S": status,
        }
    }
    update_expression = "SET " + ", ".join(f"{k} = :{k}" for k in update_fields.keys())
    expression_attribute_values = {f":{k}": v for k, v in update_fields.items()}
    kwargs = {
        "TableName": files_table,
        "Key": {
            "vcfLocation": {"S": location},
        },
        "UpdateExpression": update_expression,
        "ExpressionAttributeValues": expression_attribute_values,
    }
    response = dynamodb.update_item(**kwargs)

    return response

def deidentify(
        input_bucket, 
        output_bucket, 
        files_table, 
        project, 
        file_name, 
        object_key):

    update_deidentification_status(files_table, f"{project}/{file_name}", "Pending")

    local_input_path = f"/tmp/{file_name}" if is_lambda() else f"./{file_name}"
    local_output_path = f"/tmp/deidentified_{file_name}" if is_lambda() else f"./deidentified_{file_name}"
    
    s3.download_file(Bucket=input_bucket, Key=object_key, Filename=local_input_path)

    if any(object_key.endswith(suffix) for suffix in GENOMIC_SUFFIXES):
        deidentify_genomic()
    elif any(object_key.endswith(suffix) for suffix in METADATA_SUFFIXES):
        deidentify_metadata(local_input_path, local_output_path)

    s3.upload_file(Bucket=output_bucket, Key=object_key, Filename=local_output_path)
    s3.delete_object(Bucket=input_bucket, Key=object_key)

    update_deidentification_status(files_table, f"{project}/{file_name}", "Anonymised")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-bucket', required=True)
    parser.add_argument('--output-bucket', required=True)
    parser.add_argument('--files-table', required=True)
    parser.add_argument('--project', required=True)
    parser.add_argument('--file-name', required=True)
    parser.add_argument('--object-key', required=True)
    args = parser.parse_args()
    deidentify(
        args.input_bucket,
        args.output_bucket,
        args.files_table,
        args.project,
        args.file_name,
        args.object_key
    )
