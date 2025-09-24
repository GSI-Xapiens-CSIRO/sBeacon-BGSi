import os
import base64
import json
from datetime import datetime

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
        "pii_rekam_medis": "",
        "pii_clinical_diagnosis": "",
        "pii_symptoms": "",
        "pii_physician": "",
        "pii_genetic_counselor": ""
    }

    versions = {**json.load(open("versions.json")), **event["versions"]}
    report_id = event["report_id"]
    project = event["project"]
    vcf = event["vcf"]
    job_id = event["job_id"]
    event["timestamp"] = str(datetime.now())
    user = event.get("user", {})
    validated_at = event.get("validatedAt", "")
    validated_comment = event.get("validationComment", "")

    notes_key = f"projects/{project}/qc-figures/{vcf}/notes.txt"
    try:
        notes_obj = s3_client.get_object(Bucket=DPORTAL_BUCKET, Key=notes_key)
        notes_content = notes_obj["Body"].read().decode("utf-8")
    except Exception:
        notes_content = ""

    print("Event: ", notes_content)

    data.update(
        {
            "pii_name": "",
            "pii_dob": "",
            "pii_gender": "MALE",
            "pii_rekam_medis": "",
            "pii_clinical_diagnosis": "",
            "pii_symptoms": "",
            "pii_physician": "",
            "pii_genetic_counselor": "",
        }
    )

    # RSCM
    match event["lab"]:
        case "RSCM":

            if event.get("kind") == "neg":
                from rscm import generate_neg

                res = generate_neg(
                    **data,
                    versions=versions,
                    report_id=report_id,
                    project=project,
                    vcf=vcf,
                    user=user,
                    validated_at=validated_at,
                    validated_comment= validated_comment,
                    qc_note = notes_content
                )
            elif event.get("kind") == "pos":
                from rscm import generate_pos

                assert len(event["variants"]) > 0, "Variants not provided"
                variants = event.get("variants", [])
                variant_validations = event.get("variantValidations", {})
                res = generate_pos(
                    **data,
                    variants=variants,
                    versions=versions,
                    report_id=report_id,
                    variant_validations=variant_validations,
                    project=project,
                    vcf=vcf,
                    user=user,
                    qc_note = notes_content
                )
        case "RSIGNG":
            from igng import generate
            variants = event.get("variants", [])
            variant_validations = event.get("variantValidations", {})
            
            res = generate(
                **data,
                variants=variants,
                versions=versions,
                report_id=report_id,
                variant_validations=variant_validations,
                project=project,
                vcf=vcf,
                user=user,
                qc_note = notes_content
            )
        case "RSSARDJITO":
            from rssardjito import get_report_generator

            variants = event.get("variants", [])
            generator = get_report_generator(
                event["kind"], event["mode"], event["lang"]
            )
            if event["kind"] == "pos":
                variant_validations = event.get("variantValidations", {})
                res = generator(
                    **data,
                    variants=variants,
                    versions=versions,
                    report_id=report_id,
                    project=project,
                    vcf=vcf,
                    variant_validations=variant_validations,
                    qc_note = notes_content
                )
            else:
                res = generator(
                    **data,
                    versions=versions,
                    report_id=report_id,
                    project=project,
                    vcf=vcf,
                    user=user,
                    validated_at=validated_at,
                    validated_comment= validated_comment,
                    qc_note = notes_content
                )
        case "RSPON":
            from rspon import generate

            phenotype = event["phenotype"]
            alleles = event["alleles"]
            variants = event.get("variants", [])
            variant_validations = event.get("variantValidations", {})
            res = generate(
                **data,
                phenotype=phenotype,
                alleles=alleles,
                versions=versions,
                report_id=report_id,
                variant_validations=variant_validations,
                project=project,
                vcf=vcf,
                user=user,
                qc_note = notes_content
            )
        case "RSJPD":
            from rsjpd import generate

            data = {
                **data,
                "apoe": event.get("apoe", None),
                "slco1b1": event.get("slco1b1", None),
            }
            variants = event.get("variants", [])
            variant_validations = event.get("variantValidations", {})
            res = generate(
                **data,
                versions=versions,
                report_id=report_id,
                variant_validations=variant_validations,
                project=project,
                vcf=vcf,
                user=user,
                qc_note = notes_content
            )
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
