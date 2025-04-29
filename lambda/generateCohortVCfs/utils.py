import time

import boto3
from smart_open import open as sopen

from shared.ontoutils import get_ontology_details
from shared.utils import ENV_ATHENA, ENV_DYNAMO, ENV_COGNITO


USER_POOL_ID = ENV_COGNITO.COGNITO_USER_POOL_ID
athena = boto3.client("athena")
dynamodb = boto3.client("dynamodb")
cognito = boto3.client("cognito-idp")


def get_user_identity(sub):
    response = cognito.list_users(
        UserPoolId=USER_POOL_ID, Filter=f'sub = "{sub}"', Limit=1
    )

    assert len(response["Users"]) == 1, f"Unable to authenticate user"

    print(response["Users"][0])
    custom_identity_id = next(
        filter(
            lambda attr: attr["Name"] == "custom:identity_id",
            [attr for attr in response["Users"][0]["Attributes"]],
        )
    )["Value"]

    return custom_identity_id


def run_custom_query(
    query,
    /,
    *,
    database=ENV_ATHENA.ATHENA_METADATA_DATABASE,
    workgroup=ENV_ATHENA.ATHENA_WORKGROUP,
    queue=None,
    return_id=False,
    execution_parameters=None,
    projects=None,
    sub=None,
):
    if execution_parameters is None:
        response = athena.start_query_execution(
            QueryString=query,
            QueryExecutionContext={"Database": database},
            WorkGroup=workgroup,
        )
    else:
        response = athena.start_query_execution(
            QueryString=query,
            QueryExecutionContext={"Database": database},
            WorkGroup=workgroup,
            ExecutionParameters=execution_parameters,
        )

    retries = 0
    while True:
        exec = athena.get_query_execution(QueryExecutionId=response["QueryExecutionId"])
        status = exec["QueryExecution"]["Status"]["State"]

        if status in ("QUEUED", "RUNNING"):
            time.sleep(0.1)
            retries += 1

            if retries == 300:
                print("Timed out")
                return None
            continue
        elif status in ("FAILED", "CANCELLED"):
            print("Error: ", exec["QueryExecution"]["Status"])
            return None
        else:
            if return_id:
                return response["QueryExecutionId"]
            else:
                data = athena.get_query_results(
                    QueryExecutionId=response["QueryExecutionId"], MaxResults=1000
                )
                if queue is not None:
                    return queue.put(data["ResultSet"]["Rows"])
                else:
                    return data["ResultSet"]["Rows"]


ind_columns = [
    "id",
    "diseases",
    "ethnicity",
    "exposures",
    "geographicOrigin",
    "info",
    "interventionsOrProcedures",
    "karyotypicSex",
    "measures",
    "pedigrees",
    "phenotypicFeatures",
    "sex",
    "treatments",
]
bio_columns = [
    "id",
    "individualId",
    "biosampleStatus",
    "collectionDate",
    "collectionMoment",
    "diagnosticMarkers",
    "histologicalDiagnosis",
    "measurements",
    "obtentionProcedure",
    "pathologicalStage",
    "pathologicalTnmFinding",
    "phenotypicFeatures",
    "sampleOriginDetail",
    "sampleOriginType",
    "sampleProcessing",
    "sampleStorage",
    "tumorGrade",
    "tumorProgression",
    "info",
    "notes",
]
runs_columns = [
    "id",
    "biosampleId",
    "individualId",
    "info",
    "libraryLayout",
    "librarySelection",
    "librarySource",
    "libraryStrategy",
    "platform",
    "platformModel",
    "runDate",
]
an_columns = [
    "id",
    "_vcfSampleId",
    "individualId",
    "biosampleId",
    "runId",
    "aligner",
    "analysisDate",
    "info",
    "pipelineName",
    "pipelineRef",
    "variantCaller",
]
dst_columns = [
    "id",
    "_assemblyId",
    "_projectName",
    "_datasetName",
    "_vcfLocations",
    "_vcfChromosomeMap",
    "createDateTime",
    "dataUseConditions",
    "description",
    "externalUrl",
    "info",
    "name",
    "updateDateTime",
    "version",
]


def generate_aliases():
    ind = [f"individuals.{col} as individuals_{col.strip("_")}" for col in ind_columns]
    bio = [f"biosamples.{col} as biosamples_{col.strip("_")}" for col in bio_columns]
    runs = [f"runs.{col} as runs_{col.strip("_")}" for col in runs_columns]
    an = [f"analyses.{col} as analyses_{col.strip("_")}" for col in an_columns]
    dst = [f"datasets.{col} as datasets_{col.strip("_")}" for col in dst_columns]

    return ", ".join(ind + bio + runs + an + dst)
