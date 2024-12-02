import json
import os
from threading import Thread
from datetime import datetime, timezone

from jsonschema import Draft202012Validator, RefResolver
from shared.athena import Analysis, Biosample, Dataset, Individual, Run

from shared.utils import clear_tmp
from smart_open import open as sopen
from util import get_vcf_chromosome_maps

# uncomment below for debugging
# os.environ['LD_DEBUG'] = 'all'


def create_dataset(attributes, vcf_chromosome_maps):
    datasetId = attributes.get("datasetId", None)
    threads = []

    # dataset metadata entry information
    json_dataset = attributes.get("dataset", None)
    json_dataset["id"] = datasetId
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


def submit_dataset(body_dict):
    vcf_locations = set(body_dict.get("vcfLocations", []))
    errored, errors, vcf_chromosome_maps = get_vcf_chromosome_maps(vcf_locations)
    if errored:
        return {"success": False, "message": "\n".join(errors)}

    print("Validated the VCF files")

    try:
        create_dataset(body_dict, vcf_chromosome_maps)
    except Exception as e:
        return {"success": False, "message": f"Failed to submit dataset: {e}"}

    return {"success": True, "message": "Dataset submitted successfully"}


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


def lambda_handler(event, context):
    print("Event Received: {}".format(json.dumps(event)))

    if not event:
        return {"success": False, "message": "No body sent with request."}
    try:
        body_dict = dict()
        # json submission entry
        with sopen(event.get("s3Payload"), "r") as payload:
            body_dict.update(json.loads(payload.read()))
        # vcf files attached to the request
        body_dict["vcfLocations"] = event.get("vcfLocations", [])
        # set dataset id from project name
        body_dict["datasetId"] = f'{event.get("projectName")}:{event.get("datasetId")}'
        body_dict["dataset"]["id"] = body_dict["datasetId"]

        for individual in body_dict.get("individuals", []):
            individual["datasetId"] = body_dict["datasetId"]
        for biosample in body_dict.get("biosamples", []):
            biosample["datasetId"] = body_dict["datasetId"]
        for run in body_dict.get("runs", []):
            run["datasetId"] = body_dict["datasetId"]
        for analysis in body_dict.get("analyses", []):
            analysis["datasetId"] = body_dict["datasetId"]
        body_dict["index"] = False

    except ValueError:
        return {"success": False, "message": "Invalid JSON payload"}

    if validation_errors := validate_request(body_dict):
        print(", ".join(validation_errors))
        return {"success": False, "message": validation_errors}

    print("Validated the payload")

    result = submit_dataset(body_dict)
    # cleanup of files in /tmp caused by bcftools/tabix
    clear_tmp()
    return result


if __name__ == "__main__":
    pass
