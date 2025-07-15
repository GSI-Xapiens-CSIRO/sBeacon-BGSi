import os
import base64
import json

import boto3


s3_client = boto3.client("s3")
DPORTAL_BUCKET = os.environ.get("DPORTAL_BUCKET")


def lambda_handler(event, context):
    print("Backend Event Received: ", event)

    # TODO: connect to API
    data = {
        "pii_name": "",
        "pii_dob": "",
        "pii_gender": "Male",
    }

    versions = {**json.load(open("versions.json")), **event["versions"]}
    report_id = event["report_id"]
    project = event["project"]
    job_id = event["job_id"]

    # RSCM
    match event["lab"]:
        case "RSCM":
            from rscm import generate_neg, generate_pos

            if event["kind"] == "neg":
                res = generate_neg(**data, versions=versions, report_id=report_id)
            elif event["kind"] == "pos":
                assert len(event["variants"]) > 0, "Variants not provided"
                variants = event.get("variants", [])
                res = generate_pos(
                    **data, variants=variants, versions=versions, report_id=report_id
                )
        case "RSIGNG":
            from igng import generate

            variants = event["variants"]
            res = generate(
                **data, variants=variants, versions=versions, report_id=report_id
            )
        case "RSSARDJITO":
            from rssardjito import get_report_generator

            variants = event.get("variants", [])
            generator = get_report_generator(
                event["kind"], event["mode"], event["lang"]
            )
            if event["kind"] == "pos":
                res = generator(
                    **data, variants=variants, versions=versions, report_id=report_id
                )
            else:
                res = generator(**data, versions=versions, report_id=report_id)
        case "RSPON":
            from rspon import generate

            phenotype = event["phenotype"]
            alleles = event["alleles"]
            res = generate(
                **data,
                phenotype=phenotype,
                alleles=alleles,
                versions=versions,
                report_id=report_id,
            )
        case "RSJPD":
            from rsjpd import generate

            data = {
                **data,
                "apoe": event.get("apoe", None),
                "slco1b1": event.get("slco1b1", None),
            }
            res = generate(**data, versions=versions, report_id=report_id)
        case _:
            return {"statusCode": 400, "body": "Invalid lab or not implemented"}

    with open(res, "rb") as f:
        binary_content = f.read()

    encoded_content = base64.b64encode(binary_content).decode("utf-8")
    os.remove(res)

    # Save the report metadata to S3
    s3_client.put_object(
        Bucket=DPORTAL_BUCKET,
        Key=f"projects/{project}/clinical-workflows/{job_id}/reports/{report_id}.json",
        Body=json.dumps(event),
    )

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/octet-stream"},
        "body": encoded_content,
    }
