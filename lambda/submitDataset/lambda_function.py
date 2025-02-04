import json
import os
from threading import Thread
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator, RefResolver
from shared.athena import Analysis, Biosample, Dataset, Individual, Run

from shared.utils import clear_tmp
from smart_open import open as sopen
from util import get_vcf_chromosome_maps, get_vcfs_samples
from tabular_to_json import transform_tabular_to_json

# uncomment below for debugging
# os.environ['LD_DEBUG'] = 'all'


def create_dataset(attributes):
    vcf_locations = set(attributes.get("vcfLocations", []))
    errored, errors, vcf_chromosome_maps = get_vcf_chromosome_maps(vcf_locations)

    if errored:
        raise Exception(f"Error getting VCF chromosome maps: {errors}")

    datasetId = attributes.get("datasetId", None)
    threads = []

    # dataset metadata entry information
    json_dataset = attributes.get("dataset", None)
    json_dataset["id"] = datasetId
    json_dataset["projectName"] = attributes["projectName"]
    json_dataset["assemblyId"] = attributes["assemblyId"]
    json_dataset["vcfLocations"] = attributes["vcfLocations"]
    json_dataset["vcfChromosomeMap"] = [vcfm for vcfm in vcf_chromosome_maps]
    json_dataset["createDateTime"] = str(datetime.now(timezone.utc))
    json_dataset["updateDateTime"] = str(datetime.now(timezone.utc))
    threads.append(Thread(target=Dataset.upload_array, args=([json_dataset],)))
    threads[-1].start()

    print("De-serialising started")
    individuals = attributes.get("individuals", [])
    biosamples = attributes.get("biosamples", [])
    runs = attributes.get("runs", [])
    analyses = attributes.get("analyses", [])
    print("De-serialising complete")

    analyses_samples = set([analysis["vcfSampleId"] for analysis in analyses])
    errored, errors, vcfs_samples = get_vcfs_samples(attributes["vcfLocations"])

    if errored:
        raise Exception(f"Error getting VCF samples: {errors}")

    # check if all samples in analyses are in the VCFs
    if not analyses_samples.issubset(vcfs_samples):
        raise Exception(f"All samples in analyses not in VCFs")
    if not vcfs_samples.issubset(vcfs_samples):
        raise Exception(f"All samples in VCFs not in analyses")

    # upload to s3
    if len(individuals) > 0:
        threads.append(Thread(target=Individual.upload_array, args=(individuals,)))
        threads[-1].start()

    if len(biosamples) > 0:
        threads.append(Thread(target=Biosample.upload_array, args=(biosamples,)))
        threads[-1].start()

    if len(runs) > 0:
        threads.append(Thread(target=Run.upload_array, args=(runs,)))
        threads[-1].start()

    if len(analyses) > 0:
        threads.append(Thread(target=Analysis.upload_array, args=(analyses,)))
        threads[-1].start()

    print("Awaiting uploads")
    [thread.join() for thread in threads]
    print("Upload finished")


def validate_request(parameters):
    # load validator
    new_schema = "./schemas/submit-dataset-schema-new.json"
    schema_dir = os.path.dirname(os.path.abspath(new_schema))
    new_schema = json.load(open(new_schema))
    resolveNew = RefResolver(base_uri="file://" + schema_dir + "/", referrer=new_schema)
    validator = Draft202012Validator(new_schema, resolver=resolveNew)
    errors = []

    for error in sorted(validator.iter_errors(parameters), key=lambda e: e.path):
        error_message = f"{error.message} "
        for part in list(error.path):
            error_message += f"/{part}"
        errors.append(error_message)
    return errors


def format_info(project_name, dataset_name, additional_info):
    return {
        "projectName": project_name,
        "datasetName": dataset_name,
        "additionalInfo": additional_info,
    }


def lambda_handler(event, context):
    print("Event Received: {}".format(json.dumps(event)))

    if not event:
        return {"success": False, "message": "No body sent with request."}
    try:
        body_dict = dict()
        # json/csv/tsv submission entry
        s3payload = event.get("s3Payload")
        if type(s3payload) == str:
            if not s3payload.endswith(".json"):
                raise ValueError
            else:
                with sopen(s3payload, "r") as payload:
                    body_dict = json.loads(payload.read())
        elif type(s3payload) == dict:
            if not all(
                [
                    value.endswith(".tsv") or value.endswith(".csv")
                    for value in s3payload.values()
                ]
            ):
                raise ValueError
            else:
                body_dict = transform_tabular_to_json(s3payload)
        # vcf files attached to the request
        body_dict["vcfLocations"] = event.get("vcfLocations", [])
        project_name = event.get("projectName")  # This is a required field
        dataset_name = event.get("datasetId")
        dataset_id = f"{project_name}:{dataset_name}"

        body_dict["datasetId"] = dataset_id
        body_dict["projectName"] = project_name
        body_dict["dataset"]["datasetName"] = dataset_name
        body_dict["dataset"]["projectName"] = project_name

        for individual in body_dict.get("individuals", []):
            individual["datasetId"] = body_dict["datasetId"]
            individual["projectName"] = project_name
            individual["info"] = format_info(
                project_name, dataset_name, individual.get("info", "")
            )
        for biosample in body_dict.get("biosamples", []):
            biosample["datasetId"] = body_dict["datasetId"]
            biosample["projectName"] = project_name
            biosample["info"] = format_info(
                project_name, dataset_name, biosample.get("info", "")
            )
        for run in body_dict.get("runs", []):
            run["datasetId"] = body_dict["datasetId"]
            run["projectName"] = project_name
            run["info"] = format_info(project_name, dataset_name, run.get("info", ""))
        for analysis in body_dict.get("analyses", []):
            analysis["datasetId"] = body_dict["datasetId"]
            analysis["projectName"] = project_name
            analysis["info"] = format_info(
                project_name, dataset_name, analysis.get("info", "")
            )
        body_dict["index"] = False

    except ValueError:
        return {"success": False, "message": "Invalid payload"}

    if validation_errors := validate_request(body_dict):
        print(", ".join(validation_errors))
        return {"success": False, "message": validation_errors}

    print("Validated the payload")

    try:
        create_dataset(body_dict)
        response = {"success": True, "message": "Dataset submitted successfully"}
    except Exception as e:
        response = {"success": False, "message": str(e)}
    finally:
        # cleanup of files in /tmp caused by bcftools/tabix
        clear_tmp()

    return response


if __name__ == "__main__":
    pass
