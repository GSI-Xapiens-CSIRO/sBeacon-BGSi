import os
import base64
import json
from collections import defaultdict

import boto3

DYNAMO_SVEP_REFERENCES_TABLE = os.environ.get(
    "DYNAMO_SVEP_REFERENCES_TABLE", "svep-references"
)


def get_all_versions():
    try:
        client = boto3.client("dynamodb")
        response = client.scan(TableName=DYNAMO_SVEP_REFERENCES_TABLE)
        items = response["Items"]
        versions = {}

        while "LastEvaluatedKey" in response:
            response = client.scan(
                TableName=DYNAMO_SVEP_REFERENCES_TABLE,
                ExclusiveStartKey=response["LastEvaluatedKey"],
            )
            items.extend(response["Items"])

        for item in items:
            version = item["version"]["S"]
            tool = item["id"]["S"]
            versions[tool] = version
    except Exception as e:
        print("Error fetching versions from DynamoDB: ", e)
        versions = {}

    versions = {**versions, **json.load(open("versions.json"))}

    return versions


def lambda_handler(event, context):
    print("Backend Event Received: ", event)

    # TODO: connect to API
    data = {
        "pii_name": "",
        "pii_dob": "",
        "pii_gender": "",
    }

    versions = get_all_versions()

    # RSCM
    match event["lab"]:
        case "RSCM":
            from rscm import generate_neg, generate_pos

            if event["kind"] == "neg":
                res = generate_neg(**data, versions=versions)
            elif event["kind"] == "pos":
                assert len(event["variants"]) > 0, "Variants not provided"
                variants = event.get("variants", [])
                res = generate_pos(**data, variants=variants, versions=versions)
        case "RSIGNG":
            from igng import generate

            variants = event["variants"]
            res = generate(**data, variants=variants, versions=versions)
        case "RSSARDJITO":
            from rssardjito import get_report_generator

            variants = event.get("variants", [])
            generator = get_report_generator(
                event["kind"], event["mode"], event["lang"]
            )
            if event["kind"] == "pos":
                res = generator(**data, variants=variants, versions=versions)
            else:
                res = generator(**data, versions=versions)
        case "RSPON":
            from rspon import generate

            phenotype = event["phenotype"]
            alleles = event["alleles"]
            res = generate(
                **data, phenotype=phenotype, alleles=alleles, versions=versions
            )
        case "RSJPD":
            from rsjpd import generate

            data = {
                **data,
                "apoe": event.get("apoe", None),
                "slco1b1": event.get("slco1b1", None),
            }
            res = generate(**data)
        case _:
            return {"statusCode": 400, "body": "Invalid lab or not implemented"}

    with open(res, "rb") as f:
        binary_content = f.read()

    encoded_content = base64.b64encode(binary_content).decode("utf-8")
    os.remove(res)

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/octet-stream"},
        "body": encoded_content,
    }
