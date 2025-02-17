import json
import csv

from smart_open import open as sopen

from shared.athena import run_custom_query
from shared.dynamodb import Ontology
from shared.utils import ENV_ATHENA
from shared.apiutils import (
    RequestParams,
    build_filtering_terms_response,
    bundle_response,
)


def route(request: RequestParams, dataset_id):
    query = f"""
        SELECT DISTINCT term, label, type 
        FROM "{ENV_ATHENA.ATHENA_TERMS_TABLE}"
        WHERE term IN
        (
            SELECT DISTINCT TI.term
            FROM "{ENV_ATHENA.ATHENA_TERMS_INDEX_TABLE}" TI
            WHERE TI.id = ? and TI.kind = 'datasets'

            UNION

            SELECT DISTINCT TI.term
            FROM "{ENV_ATHENA.ATHENA_INDIVIDUALS_TABLE}" I
            JOIN 
            "{ENV_ATHENA.ATHENA_TERMS_INDEX_TABLE}" TI
            ON TI.id = I.id and TI.kind = 'individuals'
            WHERE I._datasetid = ?

            UNION

            SELECT DISTINCT TI.term
            FROM "{ENV_ATHENA.ATHENA_BIOSAMPLES_TABLE}" B
            JOIN 
            "{ENV_ATHENA.ATHENA_TERMS_INDEX_TABLE}" TI
            ON TI.id = B.id and TI.kind = 'biosamples'
            WHERE B._datasetid = ?

            UNION

            SELECT DISTINCT TI.term
            FROM "{ENV_ATHENA.ATHENA_RUNS_TABLE}" R
            JOIN 
            "{ENV_ATHENA.ATHENA_TERMS_INDEX_TABLE}" TI
            ON TI.id = R.id and TI.kind = 'runs'
            WHERE R._datasetid = ?

            UNION

            SELECT DISTINCT TI.term
            FROM "{ENV_ATHENA.ATHENA_ANALYSES_TABLE}" A
            JOIN 
            "{ENV_ATHENA.ATHENA_TERMS_INDEX_TABLE}" TI
            ON TI.id = A.id and TI.kind = 'analyses'
            WHERE A._datasetid = ?
        )
        AND (REGEXP_LIKE(label, ?) OR REGEXP_LIKE(term, ?))
        ORDER BY term
        OFFSET {request.query.pagination.skip}
        LIMIT {request.query.pagination.limit};
    """

    print("Performing query \n", query)

    if request.query._search:
        search_term = request.query._search
        regex = f"(?i).*{search_term}.*"
    else:
        regex = ".*"

    execution_parameters = [f"'{dataset_id}'"] * 5 + [regex, regex]
    exec_id = run_custom_query(
        query,
        return_id=True,
        projects=request.projects,
        sub=request.sub,
        execution_parameters=execution_parameters,
    )
    filteringTerms = []
    ontologies = set()

    with sopen(
        f"s3://{ENV_ATHENA.ATHENA_METADATA_BUCKET}/query-results/{exec_id}.csv"
    ) as s3f:
        reader = csv.reader(s3f)

        for n, row in enumerate(reader):
            if n == 0:
                continue
            term, label, typ = row
            ontologies.add(term.split(":")[0].lower())
            filteringTerms.append({"id": term, "label": label, "type": typ})

    resources = [
        ontology.attribute_values for ontology in Ontology.batch_get(ontologies)
    ]
    response = build_filtering_terms_response(filteringTerms, resources, request)

    print("Returning Response: {}".format(json.dumps(response)))
    return bundle_response(200, response)
