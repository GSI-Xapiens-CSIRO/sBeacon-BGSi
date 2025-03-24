from functools import lru_cache
from itertools import chain
import json
import os

import duckdb

REGION = os.environ["REGION"]


@lru_cache(maxsize=1000)
def fetch_term(con, term):
    if not len(term):
        return {"id": "", "label": "", "ontology": ""}
    result = con.execute(f"SELECT * FROM dictionary WHERE id = '{term}'").df()
    return result.iloc[0].to_dict()


def get_disease_codes(diseases_df, individual_id):
    if not individual_id in diseases_df.index:
        return []
    diseases_str = diseases_df.loc[individual_id].iloc[0]
    diseases = diseases_str.split(",") if diseases_str else []
    return diseases


def transform_dataset(con):
    datasets_df = con.execute("SELECT * FROM dataset").df()

    for row in datasets_df.iterrows():
        idx, data = row
        data = data.to_dict()
        dataset = {
            "id": data["id"],
            "createDateTime": data["createDateTime"],
            "dataUseConditions": {
                "duoDataUse": [
                    {
                        "id": cond,
                        "label": fetch_term(con, cond)["label"],
                        "version": ver,
                    }
                    for (cond, ver) in zip(
                        data["dataUseConditions"].split(","),
                        data["dataUseConditionsVersions"].split(","),
                    )
                ]
            },
            "description": data["description"],
            "externalUrl": data["externalUrl"],
            "info": {},
            "name": data["name"],
            "updateDateTime": data["updateDateTime"],
            "version": data["version"],
        }

    return dataset


def transform_individuals(con):
    individuals_df = con.execute("SELECT * FROM individuals").df()
    diseases_df = (
        con.execute(
            "SELECT individual_id, GROUP_CONCAT(disease, ',') diseases FROM diseases GROUP BY individual_id"
        )
        .df()
        .set_index("individual_id")
    )

    individuals = []

    for data in individuals_df.iterrows():
        idx, data = data
        data.fillna("", inplace=True)
        data = data.to_dict()
        individual = {
            "id": data["id"],
            "ethnicity": {
                "id": data["ethnicity_id"],
                "label": fetch_term(con, data["ethnicity_id"])["label"],
            },
            "geographicOrigin": {
                "id": data["geographic_origin_id"],
                "label": fetch_term(con, data["geographic_origin_id"])["label"],
            },
            "diseases": [
                {"diseaseCode": {"id": code, "label": fetch_term(con, code)["label"]}}
                for code in get_disease_codes(diseases_df, data["id"])
            ],
            "interventionsOrProcedures": [
                {"procedureCode": {"id": proc, "label": fetch_term(con, proc)["label"]}}
                for proc in (
                    data["interventions_or_procedures"].split(",")
                    if data["interventions_or_procedures"]
                    else []
                )
            ],
            "karyotypicSex": data["karyotypic_sex"],
            "sex": {
                "id": data["sex_id"],
                "label": fetch_term(con, data["sex_id"])["label"],
            },
        }
        individuals.append(individual)

    return individuals


def transform_biosamples(con):
    biosamples_df = con.execute("SELECT * FROM biosamples").df()

    biosamples = []

    for data in biosamples_df.iterrows():
        idx, data = data
        data.fillna("", inplace=True)
        data = data.to_dict()
        biosample = {
            "id": data["id"],
            "individualId": data["individual_id"],
            "biosampleStatus": {
                "id": data["biosample_status_id"],
                "label": fetch_term(con, data["biosample_status_id"])["label"],
            },
            "pathologicalTnmFinding": [
                {"id": code, "label": fetch_term(con, code)["label"]}
                for code in (
                    data["pathological_tnm_finding"].split(",")
                    if data["pathological_tnm_finding"]
                    else []
                )
            ],
            "collectionDate": data["collection_date"],
            "collectionMoment": data["collection_moment"],
            "histologicalDiagnosis": {
                "id": data["histological_diagnosis_id"],
                "label": fetch_term(con, data["histological_diagnosis_id"])["label"],
            },
            "sampleOriginType": {
                "id": data["sample_origin_type_id"],
                "label": fetch_term(con, data["sample_origin_type_id"])["label"],
            },
            "info": {},
            "notes": "",
        }

        if data["obtention_procedure_id"]:
            biosample["obtentionProcedure"] = {
                "procedureCode": {
                    "id": data["obtention_procedure_id"],
                    "label": fetch_term(con, data["obtention_procedure_id"])["label"],
                }
            }
        if data["tumor_progression_id"]:
            biosample["tumorProgression"] = {
                "id": data["tumor_progression_id"],
                "label": fetch_term(con, data["tumor_progression_id"])["label"],
            }
        if data["sample_origin_detail_id"]:
            biosample["sampleOriginDetail"] = {
                "id": data["sample_origin_detail_id"],
                "label": fetch_term(con, data["sample_origin_detail_id"])["label"],
            }
        biosamples.append(biosample)

    return biosamples


def transform_runs(con):
    runs_df = con.execute("SELECT * FROM runs").df()

    runs = []

    for data in runs_df.iterrows():
        idx, data = data
        data.fillna("", inplace=True)
        data = data.to_dict()
        run = {
            "id": data["id"],
            "biosampleId": data["biosample_id"],
            "individualId": data["individual_id"],
            "libraryLayout": data["library_layout"],
            "librarySelection": data["library_selection"],
            "librarySource": {
                "id": data["library_source"],
                "label": fetch_term(con, data["library_source"])["label"],
            },
            "libraryStrategy": data["library_strategy"],
            "platform": data["platform"],
            "platformModel": {
                "id": data["platform_model"],
                "label": fetch_term(con, data["platform_model"])["label"],
            },
            "runDate": data["run_date"],
        }
        runs.append(run)

    return runs


def transform_analyses(con):
    analyses_df = con.execute("SELECT * FROM analyses").df()

    analyses = []

    for data in analyses_df.iterrows():
        idx, data = data
        data.fillna("", inplace=True)
        data = data.to_dict()
        analysis = {
            "id": data["id"],
            "individualId": data["individual_id"],
            "biosampleId": data["biosample_id"],
            "runId": data["run_id"],
            "aligner": data["aligner"],
            "analysisDate": data["analysis_date"],
            "pipelineName": data["pipeline_name"],
            "pipelineRef": data["pipeline_ref"],
            "variantCaller": data["variant_caller"],
            "vcfSampleId": data["vcf_sample_id"],
        }
        analyses.append(analysis)

    return analyses


def transform_tabular_to_json(s3payload) -> dict:
    print("Transforming CSV/TSV to JSON")
    con = duckdb.connect("/tmp/metadata.db")
    con.execute("SET home_directory='/tmp';")
    con.execute("INSTALL httpfs; LOAD httpfs;")
    con.execute(f"SET s3_region='{REGION}';") 
    con.execute(f"SET s3_endpoint='s3.{REGION}.amazonaws.com';")
    for table, file_key in s3payload.items():
        file_extension = file_key.split(".")[-1]
        delim = "," if file_extension == "csv" else "\t"
        con.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {table} AS
            SELECT * FROM read_csv(
                '{file_key}',
                ALL_VARCHAR=TRUE,
                DELIM='{delim}'
            )"""
        )

    con.execute("SHOW TABLES").df()

    dataset = transform_dataset(con)

    individuals = transform_individuals(con)

    biosamples = transform_biosamples(con)

    runs = transform_runs(con)

    analyses = transform_analyses(con)

    body_dict = {
        "dataset": dataset,
        "assemblyId": "GRCh38",
        "individuals": individuals,
        "biosamples": biosamples,
        "runs": runs,
        "analyses": analyses,
    }

    return body_dict
